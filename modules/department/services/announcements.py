from __future__ import annotations

from collections.abc import Iterable

from django.db import transaction

from core.api.exceptions import BadRequestError, ConflictError, NotFoundError
from modules.department.domain import errors as domain_errors
from modules.department.domain import rules
from modules.department.models import Announcement, DepartmentProfile
from modules.department.selectors.scoping import announcements_for
from modules.department.services import notifications
from modules.department.services.authz import require, require_department


@transaction.atomic
def create_announcement(
    *,
    department_id: int,
    actor,
    title: str,
    content: str,
    target_roles: Iterable[str],
    target_programs: Iterable[str] = (),
    target_academic_years: Iterable[str] = (),
) -> Announcement:
    # UC-DEPT-002 / BR-DEPT-001 / BR-DEPT-003 / AFR-DEPT-001 / AFR-DEPT-046.
    require(actor, "department.announcement.create")
    dept = require_department(actor, department_id)
    try:
        roles, programs, years = rules.validate_announcement_payload(
            title=title,
            content=content,
            target_roles=target_roles,
            target_programs=target_programs,
            target_academic_years=target_academic_years,
        )
    except domain_errors.ValidationRuleError as exc:
        raise BadRequestError(exc.message, code=exc.code) from exc

    ann = Announcement.objects.create(
        department=dept,
        title=title.strip(),
        content=content.strip(),
        target_roles=roles,
        target_programs=programs,
        target_academic_years=years,
        status="active",
        created_by_user_id=actor.user_id,
    )

    # AFR-DEPT-046: notify matching Students and Faculty in target scope.
    profiles = DepartmentProfile.objects.filter(
        department=dept, profile_kind__in=("student", "faculty")
    )
    for prof in profiles:
        if rules.announcement_matches_viewer(
            target_roles=roles,
            target_programs=programs,
            target_academic_years=years,
            viewer_role=prof.profile_kind,
            viewer_program=prof.program,
            viewer_academic_year=prof.academic_year,
        ):
            notifications.enqueue(
                department=dept,
                topic="announcement.published",
                dedupe_key=f"dept.ann.published:{ann.pk}:{prof.user_id}",
                recipient_user_id=prof.user_id,
                subject=f"[{dept.code}] {ann.title}",
                body=ann.content,
                payload={"announcement_id": ann.pk, "department_id": dept.pk},
            )
    return ann


@transaction.atomic
def update_announcement(
    *,
    announcement_id: int,
    actor,
    title: str | None = None,
    content: str | None = None,
    target_roles: Iterable[str] | None = None,
    target_programs: Iterable[str] | None = None,
    target_academic_years: Iterable[str] | None = None,
) -> Announcement:
    # UC-DEPT-003 / BR-DEPT-004 / BR-DEPT-003 / AFR-DEPT-004.
    require(actor, "department.announcement.update")
    ann = announcements_for(actor).select_for_update().filter(pk=announcement_id).first()
    if ann is None:
        raise NotFoundError("Announcement not found.", code="announcement_not_found")
    if ann.status != "active":
        raise ConflictError(
            "Only active announcements can be edited.", code="announcement_inactive"
        )

    new_title = ann.title if title is None else title
    new_content = ann.content if content is None else content
    new_roles = ann.target_roles if target_roles is None else target_roles
    new_programs = ann.target_programs if target_programs is None else target_programs
    new_years = (
        ann.target_academic_years if target_academic_years is None else target_academic_years
    )

    try:
        roles, programs, years = rules.validate_announcement_payload(
            title=new_title,
            content=new_content,
            target_roles=new_roles,
            target_programs=new_programs,
            target_academic_years=new_years,
        )
    except domain_errors.ValidationRuleError as exc:
        raise BadRequestError(exc.message, code=exc.code) from exc

    ann.title = new_title.strip()
    ann.content = new_content.strip()
    ann.target_roles = roles
    ann.target_programs = programs
    ann.target_academic_years = years
    ann.updated_by_user_id = actor.user_id
    ann.save(
        update_fields=[
            "title",
            "content",
            "target_roles",
            "target_programs",
            "target_academic_years",
            "updated_by_user_id",
            "updated_at",
        ]
    )
    return ann


@transaction.atomic
def hide_announcement(*, announcement_id: int, actor) -> Announcement:
    # UC-DEPT-003 / BR-DEPT-004 / AFR-DEPT-005.
    require(actor, "department.announcement.update")
    ann = announcements_for(actor).select_for_update().filter(pk=announcement_id).first()
    if ann is None:
        raise NotFoundError("Announcement not found.", code="announcement_not_found")
    if ann.status != "active":
        raise ConflictError(
            "Only active announcements can be hidden.", code="announcement_inactive"
        )
    ann.status = "hidden"
    ann.updated_by_user_id = actor.user_id
    ann.save(update_fields=["status", "updated_by_user_id", "updated_at"])
    return ann


@transaction.atomic
def delete_announcement(*, announcement_id: int, actor) -> Announcement:
    # UC-DEPT-003 / BR-DEPT-004 / AFR-DEPT-006.
    require(actor, "department.announcement.delete")
    ann = announcements_for(actor).select_for_update().filter(pk=announcement_id).first()
    if ann is None:
        raise NotFoundError("Announcement not found.", code="announcement_not_found")
    if ann.status == "deleted":
        raise ConflictError("Announcement is already deleted.", code="announcement_deleted")
    ann.status = "deleted"
    ann.updated_by_user_id = actor.user_id
    ann.save(update_fields=["status", "updated_by_user_id", "updated_at"])
    return ann
