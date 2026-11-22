from __future__ import annotations

from django.db.models import QuerySet

from modules.department.domain import rules
from modules.department.domain import state_machine as sm
from modules.department.models import (
    Announcement,
    CourseEnrollment,
    Department,
    DepartmentProfile,
    DepartmentProgram,
    DepartmentRoleAssignment,
    Feedback,
    InventoryItem,
    LabResource,
    OfficialDetailChange,
    StockMovement,
    StockRequest,
    TimetableSlot,
)

# Map ERP designation names to normalized Department.code values.
_DESIGNATION_DEPT_MAP: dict[str, str] = {
    "hod (cse)": "CSE",
    "hod (design)": "DESIGN",
    "hod (ece)": "ECE",
    "hod (liberal arts)": "LA",
    "hod (me)": "ME",
    "hod (ns)": "NS",
    "deptadmin_cse": "CSE",
    "deptadmin_design": "DESIGN",
    "deptadmin_ece": "ECE",
    "deptadmin_liberalarts": "LA",
    "deptadmin_me": "ME",
    "deptadmin_ns": "NS",
    "deptadmin_sm": "SM",
}


def actor_lane(actor) -> str:
    # Derive lane from the active role and its active permissions, never a union of held roles.
    active = (getattr(actor, "active_role", None) or getattr(actor, "kind", "") or "").strip()
    low = active.lower()
    if low == "acadadmin" or _has(actor, "department.role_assignment.assign"):
        return sm.ACTOR_INSTITUTE_ADMIN
    if low.startswith("hod") or _has(actor, "department.stock_request.approve"):
        return sm.ACTOR_HOD
    if low.startswith("deptadmin") or low == "dept_admin" or _has(
        actor, "department.feedback.review", "department.inventory.create"
    ):
        return sm.ACTOR_DEPT_ADMIN
    if low == "faculty" or getattr(actor, "kind", None) == "faculty":
        return sm.ACTOR_FACULTY
    if low == "student" or getattr(actor, "kind", None) == "student":
        return sm.ACTOR_STUDENT
    return "other"


def _has(actor, *codes: str) -> bool:
    check = getattr(actor, "has_permission", None)
    return bool(check) and any(check(c) for c in codes)


def _own_id(actor) -> int | None:
    return getattr(actor, "user_id", None)


def scoped_department_codes(actor) -> set[str] | None:
    # None means institute-wide (e.g. acadadmin or generic dept_admin); set narrows to departments.
    active = (getattr(actor, "active_role", None) or "").strip().lower()
    if active in _DESIGNATION_DEPT_MAP:
        return {_DESIGNATION_DEPT_MAP[active]}
    if active in ("acadadmin", "dept_admin"):
        return None
    uid = _own_id(actor)
    if uid is None:
        return set()
    profile_codes = set(
        DepartmentProfile.objects.filter(user_id=uid).values_list("department__code", flat=True)
    )
    if profile_codes:
        return profile_codes
    return None


def _filter_dept(qs: QuerySet, actor, field: str = "department__code") -> QuerySet:
    codes = scoped_department_codes(actor)
    if codes is None:
        return qs
    if not codes:
        return qs.none()
    return qs.filter(**{f"{field}__in": codes})


def departments_for(actor) -> QuerySet[Department]:
    return _filter_dept(Department.objects.all(), actor, field="code")


def official_changes_for(actor) -> QuerySet[OfficialDetailChange]:
    lane = actor_lane(actor)
    if lane not in (sm.ACTOR_HOD, sm.ACTOR_DEPT_ADMIN):
        return OfficialDetailChange.objects.none()
    return _filter_dept(OfficialDetailChange.objects.select_related("department"), actor)


def announcements_for(actor) -> QuerySet[Announcement]:
    # BR-DEPT-002: filter active announcements by viewer role, program, and academic year.
    base = _filter_dept(Announcement.objects.select_related("department"), actor)
    lane = actor_lane(actor)
    if lane == sm.ACTOR_HOD:
        return base.exclude(status="deleted")

    active_qs = base.filter(status="active")
    uid = _own_id(actor)
    if uid is None:
        return active_qs.none()

    profile = (
        DepartmentProfile.objects.filter(user_id=uid)
        .values("program", "academic_year")
        .first()
    )
    viewer_program = (profile or {}).get("program", "")
    viewer_year = (profile or {}).get("academic_year", "")

    matched_ids = [
        ann.pk
        for ann in active_qs
        if rules.announcement_matches_viewer(
            target_roles=ann.target_roles,
            target_programs=ann.target_programs,
            target_academic_years=ann.target_academic_years,
            viewer_role=lane,
            viewer_program=viewer_program,
            viewer_academic_year=viewer_year,
        )
    ]
    return active_qs.filter(pk__in=matched_ids)


def inventory_for(actor) -> QuerySet[InventoryItem]:
    lane = actor_lane(actor)
    if lane not in (sm.ACTOR_FACULTY, sm.ACTOR_HOD, sm.ACTOR_DEPT_ADMIN):
        return InventoryItem.objects.none()
    return _filter_dept(InventoryItem.objects.select_related("department"), actor)


def stock_requests_for(actor) -> QuerySet[StockRequest]:
    base = _filter_dept(StockRequest.objects.select_related("department", "item"), actor)
    lane = actor_lane(actor)
    if lane in (sm.ACTOR_HOD, sm.ACTOR_DEPT_ADMIN):
        return base
    if lane == sm.ACTOR_FACULTY:
        own = _own_id(actor)
        return base.filter(requester_user_id=own) if own is not None else base.none()
    return base.none()


def stock_movements_for(actor) -> QuerySet[StockMovement]:
    # BR-DEPT-012 / AFR-DEPT-016: Faculty sees only their own issued-stock history.
    base = _filter_dept(
        StockMovement.objects.select_related("department", "item", "stock_request"), actor
    )
    lane = actor_lane(actor)
    if lane in (sm.ACTOR_HOD, sm.ACTOR_DEPT_ADMIN):
        return base
    if lane == sm.ACTOR_FACULTY:
        own = _own_id(actor)
        if own is None:
            return base.none()
        return base.filter(movement_type="issuance", stock_request__requester_user_id=own)
    return base.none()


def feedback_for(actor) -> QuerySet[Feedback]:
    # BR-DEPT-017 / BR-DEPT-018: confidential scoping + HOD sees only post-initial-review rows.
    base = _filter_dept(Feedback.objects.select_related("department"), actor)
    lane = actor_lane(actor)
    if lane == sm.ACTOR_DEPT_ADMIN:
        return base
    if lane == sm.ACTOR_HOD:
        return base.filter(status__in=(sm.FEEDBACK_UNDER_REVIEW, sm.FEEDBACK_RESOLVED,
                                       sm.FEEDBACK_CLOSED))
    if lane in (sm.ACTOR_STUDENT, sm.ACTOR_FACULTY):
        own = _own_id(actor)
        return base.filter(submitter_user_id=own) if own is not None else base.none()
    return base.none()


def timetables_for(actor) -> QuerySet[TimetableSlot]:
    return _filter_dept(
        TimetableSlot.objects.select_related("department").filter(is_active=True), actor
    )


def lab_resources_for(actor) -> QuerySet[LabResource]:
    # BR-DEPT-012: Faculty, HOD, and Dept_Admin view lab resource profiles.
    lane = actor_lane(actor)
    if lane not in (sm.ACTOR_FACULTY, sm.ACTOR_HOD, sm.ACTOR_DEPT_ADMIN):
        return LabResource.objects.none()
    return _filter_dept(LabResource.objects.select_related("department"), actor)


def programs_for(actor) -> QuerySet[DepartmentProgram]:
    return _filter_dept(
        DepartmentProgram.objects.select_related("department").filter(is_active=True), actor
    )


def role_assignments_for(actor) -> QuerySet[DepartmentRoleAssignment]:
    lane = actor_lane(actor)
    if lane != sm.ACTOR_INSTITUTE_ADMIN:
        return DepartmentRoleAssignment.objects.none()
    return DepartmentRoleAssignment.objects.select_related("department")


def enrollments_for(actor) -> QuerySet[CourseEnrollment]:
    base = _filter_dept(CourseEnrollment.objects.select_related("department"), actor)
    lane = actor_lane(actor)
    if lane in (sm.ACTOR_HOD, sm.ACTOR_DEPT_ADMIN):
        return base
    if lane == sm.ACTOR_FACULTY:
        own = _own_id(actor)
        return base.filter(faculty_user_id=own) if own is not None else base.none()
    return base.none()
