from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from core.api.exceptions import BadRequestError, ConflictError, NotFoundError, PermissionDeniedError
from modules.department.domain import errors as domain_errors
from modules.department.domain import rules
from modules.department.domain import state_machine as sm
from modules.department.models import Department, OfficialDetailChange
from modules.department.selectors.scoping import actor_lane, official_changes_for
from modules.department.services.authz import require, require_department


@transaction.atomic
def update_general_details(
    *,
    department_id: int,
    actor,
    description: str | None = None,
    contact_email: str | None = None,
    location: str | None = None,
    website_url: str | None = None,
) -> Department:
    # UC-DEPT-010 / AFR-DEPT-038: Dept_Admin updates general non-official department info.
    require(actor, "department.department.update")
    dept = require_department(actor, department_id)
    dept = Department.objects.select_for_update().get(pk=dept.pk)
    fields = ["updated_at"]
    if description is not None:
        dept.description = description.strip()
        fields.append("description")
    if contact_email is not None:
        dept.contact_email = contact_email.strip()
        fields.append("contact_email")
    if location is not None:
        dept.location = location.strip()
        fields.append("location")
    if website_url is not None:
        dept.website_url = website_url.strip()
        fields.append("website_url")
    dept.save(update_fields=fields)
    return dept


@transaction.atomic
def propose_official_change(
    *,
    department_id: int,
    actor,
    field_name: str,
    proposed_value: str,
) -> OfficialDetailChange:
    # UC-DEPT-010 / BR-DEPT-011 / AFR-DEPT-039 / AFR-DEPT-053 / BW-DEPT-05 / BW-DEPT-06.
    require(actor, "department.department.update")
    dept = require_department(actor, department_id)
    try:
        clean_field = rules.validate_official_change_field(field_name, proposed_value)
    except domain_errors.ForbiddenOfficialField as exc:
        raise BadRequestError(exc.message, code=exc.code) from exc
    except domain_errors.ValidationRuleError as exc:
        raise BadRequestError(exc.message, code=exc.code) from exc

    previous = getattr(dept, clean_field, "") or ""
    return OfficialDetailChange.objects.create(
        department=dept,
        field_name=clean_field,
        previous_value=previous,
        proposed_value=proposed_value.strip(),
        status=sm.OFFICIAL_PENDING,
        proposed_by_user_id=actor.user_id,
    )


@transaction.atomic
def decide_official_change(
    *,
    change_id: int,
    actor,
    approve: bool,
    note: str = "",
) -> OfficialDetailChange:
    # UC-DEPT-012 / BR-DEPT-013 / AFR-DEPT-040 / BW-DEPT-05 / BW-DEPT-06 / CW-DEPT-03.
    require(actor, "department.official_change.approve")
    change = (
        official_changes_for(actor)
        .select_for_update()
        .select_related("department")
        .filter(pk=change_id)
        .first()
    )
    if change is None:
        raise NotFoundError("Official change request not found.", code="official_change_not_found")
    if change.proposed_by_user_id == actor.user_id:
        raise ConflictError(
            "You cannot approve or reject an official change you proposed.",
            code="self_approval_forbidden",
        )

    target = sm.OFFICIAL_APPROVED if approve else sm.OFFICIAL_REJECTED
    try:
        sm.resolve("official_change", change.status, target, actor_lane(actor))
    except domain_errors.ActorNotAllowed as exc:
        raise PermissionDeniedError(exc.message, code=exc.code) from exc
    except domain_errors.InvalidTransition as exc:
        raise ConflictError(exc.message, code=exc.code) from exc

    change.status = target
    change.decided_by_user_id = actor.user_id
    change.decided_at = timezone.now()
    change.decision_note = note.strip()[:300]
    change.save(
        update_fields=["status", "decided_by_user_id", "decided_at", "decision_note", "updated_at"]
    )

    if approve:
        dept = Department.objects.select_for_update().get(pk=change.department_id)
        setattr(dept, change.field_name, change.proposed_value)
        dept.save(update_fields=[change.field_name, "updated_at"])
    return change
