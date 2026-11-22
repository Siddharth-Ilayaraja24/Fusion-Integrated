from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from core.api.exceptions import BadRequestError, ConflictError, NotFoundError, PermissionDeniedError
from modules.department.domain import errors as domain_errors
from modules.department.domain import state_machine as sm
from modules.department.models import Feedback, FeedbackTransition
from modules.department.selectors.scoping import actor_lane, feedback_for
from modules.department.services import notifications
from modules.department.services.authz import require, require_department


@transaction.atomic
def submit_feedback(
    *,
    department_id: int,
    actor,
    subject: str,
    body: str,
) -> Feedback:
    # UC-DEPT-007 / BR-DEPT-008 / BR-DEPT-017 / AFR-DEPT-017 / AFR-DEPT-018 / AFR-DEPT-044.
    require(actor, "department.feedback.create")
    lane = actor_lane(actor)
    if lane not in (sm.ACTOR_STUDENT, sm.ACTOR_FACULTY):
        raise PermissionDeniedError(
            "Only authenticated Students and Faculty may submit department feedback.",
            code="feedback_submit_not_allowed",
        )
    dept = require_department(actor, department_id)
    if not (subject or "").strip() or not (body or "").strip():
        raise BadRequestError(
            "Feedback subject and body are required.", code="missing_feedback_content"
        )

    fb = Feedback.objects.create(
        department=dept,
        submitter_user_id=actor.user_id,
        submitter_role=lane,
        subject=subject.strip()[:200],
        body=body.strip(),
        status=sm.FEEDBACK_NEW,
    )
    # AFR-DEPT-044: notify Dept_Admin when new feedback is submitted.
    notifications.enqueue(
        department=dept,
        topic="feedback.submitted",
        dedupe_key=f"dept.fb.submitted:{fb.pk}",
        recipient_user_id=dept.active_dept_admin_user_id,
        subject=f"[{dept.code}] New confidential feedback #{fb.pk}",
        body=f"New feedback submitted for initial review: {fb.subject}",
        payload={"feedback_id": fb.pk},
    )
    return fb


@transaction.atomic
def review_feedback(
    *,
    feedback_id: int,
    actor,
    category: str,
    close_as_simple: bool = False,
    note: str = "",
) -> Feedback:
    # UC-DEPT-008 / BR-DEPT-018 / AFR-DEPT-019..021 / BW-DEPT-03 / CW-DEPT-02.
    require(actor, "department.feedback.review")
    fb = (
        feedback_for(actor)
        .select_for_update()
        .select_related("department")
        .filter(pk=feedback_id)
        .first()
    )
    if fb is None:
        raise NotFoundError("Feedback not found.", code="feedback_not_found")
    if fb.submitter_user_id == actor.user_id:
        raise ConflictError(
            "You cannot review your own feedback submission.",
            code="self_approval_forbidden",
        )
    clean_cat = (category or "").strip()
    if not clean_cat:
        raise BadRequestError(
            "A category is required during initial feedback review.",
            code="missing_category",
        )

    target = sm.FEEDBACK_CLOSED if close_as_simple else sm.FEEDBACK_UNDER_REVIEW
    lane = actor_lane(actor)
    try:
        sm.resolve("feedback", fb.status, target, lane)
    except domain_errors.ActorNotAllowed as exc:
        raise PermissionDeniedError(exc.message, code=exc.code) from exc
    except domain_errors.InvalidTransition as exc:
        raise ConflictError(exc.message, code=exc.code) from exc

    now = timezone.now()
    frm = fb.status
    fb.category = clean_cat[:80]
    fb.status = target
    fb.initial_reviewed_by_user_id = actor.user_id
    fb.initial_reviewed_at = now
    update_fields = [
        "category",
        "status",
        "initial_reviewed_by_user_id",
        "initial_reviewed_at",
        "updated_at",
    ]
    if close_as_simple:
        fb.resolved_by_user_id = actor.user_id
        fb.resolved_at = now
        fb.resolution_note = note.strip()
        update_fields += ["resolved_by_user_id", "resolved_at", "resolution_note"]
    fb.save(update_fields=update_fields)

    FeedbackTransition.objects.create(
        feedback=fb,
        from_status=frm,
        to_status=target,
        actor_user_id=actor.user_id,
        actor_role=lane,
        note=note.strip()[:300],
    )

    if close_as_simple:
        _notify_terminal(fb)
    return fb


@transaction.atomic
def dispose_feedback(
    *,
    feedback_id: int,
    actor,
    status: str,
    note: str = "",
) -> Feedback:
    # UC-DEPT-008 / UC-DEPT-014 / BR-DEPT-009 / BR-DEPT-018 / BW-DEPT-03 / BW-DEPT-04 / CW-DEPT-02.
    require(actor, "department.feedback.update")
    fb = (
        feedback_for(actor)
        .select_for_update()
        .select_related("department")
        .filter(pk=feedback_id)
        .first()
    )
    if fb is None:
        raise NotFoundError("Feedback not found.", code="feedback_not_found")
    if fb.submitter_user_id == actor.user_id:
        raise ConflictError(
            "You cannot resolve or close your own feedback submission.",
            code="self_approval_forbidden",
        )
    # BR-DEPT-018: disposition requires initial review via review_feedback first.
    if fb.status == sm.FEEDBACK_NEW:
        raise ConflictError(
            "Feedback must undergo initial review before disposition.",
            code="initial_review_required",
        )

    target = (status or "").strip().lower()
    if target not in (sm.FEEDBACK_RESOLVED, sm.FEEDBACK_CLOSED):
        raise BadRequestError(
            "Disposition status must be 'resolved' or 'closed'.",
            code="invalid_disposition_status",
        )

    lane = actor_lane(actor)
    try:
        sm.resolve("feedback", fb.status, target, lane)
    except domain_errors.ActorNotAllowed as exc:
        raise PermissionDeniedError(exc.message, code=exc.code) from exc
    except domain_errors.InvalidTransition as exc:
        raise ConflictError(exc.message, code=exc.code) from exc

    frm = fb.status
    fb.status = target
    fb.resolved_by_user_id = actor.user_id
    fb.resolved_at = timezone.now()
    fb.resolution_note = note.strip()
    fb.save(
        update_fields=[
            "status",
            "resolved_by_user_id",
            "resolved_at",
            "resolution_note",
            "updated_at",
        ]
    )
    FeedbackTransition.objects.create(
        feedback=fb,
        from_status=frm,
        to_status=target,
        actor_user_id=actor.user_id,
        actor_role=lane,
        note=note.strip()[:300],
    )
    _notify_terminal(fb)
    return fb


def _notify_terminal(fb: Feedback) -> None:
    # AFR-DEPT-045: notify feedback submitter when marked Resolved or Closed.
    notifications.enqueue(
        department=fb.department,
        topic=f"feedback.{fb.status}",
        dedupe_key=f"dept.fb.terminal:{fb.pk}:{fb.status}",
        recipient_user_id=fb.submitter_user_id,
        subject=f"[{fb.department.code}] Feedback #{fb.pk} marked {fb.status}",
        body=f"Your feedback '{fb.subject}' has been marked {fb.status}.",
        payload={"feedback_id": fb.pk, "status": fb.status},
    )
