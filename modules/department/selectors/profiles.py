from __future__ import annotations

from modules.department.domain import rules
from modules.department.domain import state_machine as sm
from modules.department.models import CourseEnrollment, DepartmentProfile
from modules.department.selectors.scoping import actor_lane, scoped_department_codes


def _snapshot(p: DepartmentProfile) -> rules.ProfileSnapshot:
    return rules.ProfileSnapshot(
        id=p.pk,
        department_id=p.department_id,
        user_id=p.user_id,
        profile_kind=p.profile_kind,
        display_name=p.display_name,
        email=p.email,
        program=p.program,
        academic_year=p.academic_year,
        designation_title=p.designation_title,
        office_room=p.office_room,
        research_area=p.research_area,
        graduation_year=p.graduation_year,
        current_affiliation=p.current_affiliation,
        academic_notes=p.academic_notes,
    )


def _visible_profiles_qs(actor):
    qs = DepartmentProfile.objects.select_related("department")
    codes = scoped_department_codes(actor)
    if codes is not None:
        if not codes:
            return qs.none()
        qs = qs.filter(department__code__in=codes)
    return qs


def _enrolled_student_ids(actor) -> set[int]:
    uid = getattr(actor, "user_id", None)
    if uid is None:
        return set()
    return set(
        CourseEnrollment.objects.filter(faculty_user_id=uid).values_list(
            "student_user_id", flat=True
        )
    )


def list_visible_profiles(actor, *, department_id: int | None = None,
                          profile_kind: str | None = None) -> list[dict]:
    # BR-DEPT-019: project each visible profile according to viewer role and course relationship.
    lane = actor_lane(actor)
    if lane not in (sm.ACTOR_STUDENT, sm.ACTOR_FACULTY, sm.ACTOR_HOD, sm.ACTOR_DEPT_ADMIN):
        return []
    qs = _visible_profiles_qs(actor)
    if department_id is not None:
        qs = qs.filter(department_id=department_id)
    if profile_kind:
        qs = qs.filter(profile_kind=profile_kind)

    enrolled = _enrolled_student_ids(actor) if lane == sm.ACTOR_FACULTY else set()
    uid = getattr(actor, "user_id", None)

    out: list[dict] = []
    for prof in qs:
        projected = rules.project_profile_fields(
            _snapshot(prof),
            viewer_role=lane,
            viewer_user_id=uid,
            is_course_instructor=prof.user_id in enrolled,
        )
        if projected is not None:
            out.append(projected)
    return out


def get_visible_profile(actor, profile_id: int) -> dict | None:
    # Returns None when out of scope so the view answers 404, never 403.
    lane = actor_lane(actor)
    if lane not in (sm.ACTOR_STUDENT, sm.ACTOR_FACULTY, sm.ACTOR_HOD, sm.ACTOR_DEPT_ADMIN):
        return None
    prof = _visible_profiles_qs(actor).filter(pk=profile_id).first()
    if prof is None:
        return None
    enrolled = _enrolled_student_ids(actor) if lane == sm.ACTOR_FACULTY else set()
    return rules.project_profile_fields(
        _snapshot(prof),
        viewer_role=lane,
        viewer_user_id=getattr(actor, "user_id", None),
        is_course_instructor=prof.user_id in enrolled,
    )
