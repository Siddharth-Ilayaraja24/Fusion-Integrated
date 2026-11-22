from __future__ import annotations

from datetime import datetime

from django.db import transaction
from django.utils import timezone

from core.api.exceptions import BadRequestError, ConflictError, NotFoundError
from modules.department.domain import errors as domain_errors
from modules.department.domain import rules
from modules.department.domain import state_machine as sm
from modules.department.models import Department, DepartmentRoleAssignment
from modules.department.services.authz import require


@transaction.atomic
def assign_role(
    *,
    department_id: int,
    actor,
    role_type: str,
    user_id: int,
    valid_from: datetime,
    valid_to: datetime,
) -> DepartmentRoleAssignment:
    # UC-DEPT-020 / BR-DEPT-021 / BR-DEPT-022 / BR-DEPT-023 / AFR-DEPT-047..053.
    require(actor, "department.role_assignment.assign")
    dept = Department.objects.select_for_update().filter(pk=department_id).first()
    if dept is None:
        raise NotFoundError("Department not found.", code="department_not_found")

    clean_role = (role_type or "").strip().lower()
    if clean_role not in ("hod", "dept_admin"):
        raise BadRequestError("role_type must be 'hod' or 'dept_admin'.", code="invalid_role_type")

    try:
        rules.validate_role_tenure(valid_from, valid_to)
    except domain_errors.InvalidTenure as exc:
        raise BadRequestError(exc.message, code=exc.code) from exc

    now = timezone.now()
    if valid_to <= now:
        raise BadRequestError("valid_to must be in the future.", code="tenure_already_ended")

    # Reject overlapping scheduled assignments for the same department and role_type.
    overlap = DepartmentRoleAssignment.objects.filter(
        department=dept,
        role_type=clean_role,
        status=sm.ROLE_SCHEDULED,
        valid_from__lt=valid_to,
        valid_to__gt=valid_from,
    ).exists()
    if overlap:
        raise ConflictError(
            "Another scheduled assignment overlaps that validity interval for this role.",
            code="overlapping_role_assignment",
        )

    assignment = DepartmentRoleAssignment.objects.create(
        department=dept,
        role_type=clean_role,
        user_id=user_id,
        valid_from=valid_from,
        valid_to=valid_to,
        status=sm.ROLE_SCHEDULED,
        assigned_by_user_id=actor.user_id,
    )

    # If valid_from is already reached, apply UC-DEPT-022 immediately inside this transaction.
    if valid_from <= now:
        _activate_locked(dept, assignment, now)
    return assignment


def apply_effective_transitions(*, now: datetime | None = None) -> int:
    # UC-DEPT-022 / BR-DEPT-022 / BR-DEPT-024 / BW-DEPT-07 / BW-DEPT-08 / CW-DEPT-04.
    now = now or timezone.now()
    changed = 0

    dept_ids = list(
        Department.objects.order_by("id").values_list("id", flat=True)
    )
    for dept_id in dept_ids:
        with transaction.atomic():
            dept = Department.objects.select_for_update().get(pk=dept_id)
            for role_type in ("hod", "dept_admin"):
                # Expire any active assignment whose tenure has ended.
                active = (
                    DepartmentRoleAssignment.objects.select_for_update()
                    .filter(department=dept, role_type=role_type, status=sm.ROLE_ACTIVE)
                    .first()
                )
                if active is not None and active.valid_to <= now:
                    sm.resolve("role_assignment", active.status, sm.ROLE_EXPIRED, sm.ACTOR_SYSTEM)
                    active.status = sm.ROLE_EXPIRED
                    active.revoked_at = now
                    active.save(update_fields=["status", "revoked_at", "updated_at"])
                    _sync_department_holder(dept, role_type, None)
                    changed += 1

                # Activate the latest due scheduled assignment whose window is still open.
                due = (
                    DepartmentRoleAssignment.objects.select_for_update()
                    .filter(
                        department=dept,
                        role_type=role_type,
                        status=sm.ROLE_SCHEDULED,
                        valid_from__lte=now,
                        valid_to__gt=now,
                    )
                    .order_by("-valid_from", "-id")
                    .first()
                )
                if due is not None:
                    _activate_locked(dept, due, now)
                    changed += 1
    return changed


def _activate_locked(dept: Department, incoming: DepartmentRoleAssignment, now: datetime) -> None:
    # Revoke outgoing active holder first so the partial unique constraint always holds.
    outgoing = (
        DepartmentRoleAssignment.objects.select_for_update()
        .filter(department=dept, role_type=incoming.role_type, status=sm.ROLE_ACTIVE)
        .exclude(pk=incoming.pk)
        .first()
    )
    if outgoing is not None:
        sm.resolve("role_assignment", outgoing.status, sm.ROLE_SUPERSEDED, sm.ACTOR_SYSTEM)
        outgoing.status = sm.ROLE_SUPERSEDED
        outgoing.revoked_at = now
        outgoing.save(update_fields=["status", "revoked_at", "updated_at"])

    sm.resolve("role_assignment", incoming.status, sm.ROLE_ACTIVE, sm.ACTOR_SYSTEM)
    incoming.status = sm.ROLE_ACTIVE
    incoming.activated_at = now
    incoming.save(update_fields=["status", "activated_at", "updated_at"])
    _sync_department_holder(dept, incoming.role_type, incoming.user_id)


def _sync_department_holder(dept: Department, role_type: str, user_id: int | None) -> None:
    # AFR-DEPT-053: synchronize displayed Headship from the active HOD assignment.
    if role_type == "hod":
        dept.active_hod_user_id = user_id
        dept.save(update_fields=["active_hod_user_id", "updated_at"])
    else:
        dept.active_dept_admin_user_id = user_id
        dept.save(update_fields=["active_dept_admin_user_id", "updated_at"])
