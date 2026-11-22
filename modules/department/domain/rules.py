from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, time

from modules.department.domain.errors import (
    ForbiddenOfficialField,
    InsufficientStock,
    InvalidTenure,
    TimetableConflict,
    ValidationRuleError,
)

# BR-DEPT-001 / BR-DEPT-002: valid announcement target roles.
VALID_TARGET_ROLES = frozenset({"student", "faculty", "dept_admin", "hod", "all"})

# BR-DEPT-011 / AFR-DEPT-053: Headship is centrally derived, never edited via official change.
EDITABLE_OFFICIAL_FIELDS = frozenset({"name", "core_policies"})
FORBIDDEN_OFFICIAL_FIELDS = frozenset({"headship", "hod", "active_hod_user_id"})


@dataclass(frozen=True)
class TimetableSlotSpec:
    slot_id: int | None
    department_id: int
    day_of_week: int
    start_time: time
    end_time: time
    room: str
    faculty_user_id: int | None
    program: str
    academic_year: str
    section: str


@dataclass(frozen=True)
class ProfileSnapshot:
    id: int
    department_id: int
    user_id: int
    profile_kind: str
    display_name: str
    email: str
    program: str
    academic_year: str
    designation_title: str
    office_room: str
    research_area: str
    graduation_year: int | None
    current_affiliation: str
    academic_notes: str


def validate_announcement_payload(
    *,
    title: str,
    content: str,
    target_roles: Iterable[str],
    target_programs: Iterable[str],
    target_academic_years: Iterable[str],
) -> tuple[list[str], list[str], list[str]]:
    # BR-DEPT-003: non-empty content and sufficient target-scope metadata required.
    if not (title or "").strip():
        raise ValidationRuleError("Announcement title is required.", code="missing_title")
    if not (content or "").strip():
        raise ValidationRuleError("Announcement content is required.", code="missing_content")

    roles = sorted({r.strip().lower() for r in target_roles if str(r).strip()})
    programs = sorted({str(p).strip() for p in target_programs if str(p).strip()})
    years = sorted({str(y).strip() for y in target_academic_years if str(y).strip()})

    if not roles:
        raise ValidationRuleError(
            "At least one target role is required for publication.",
            code="missing_target_scope",
        )
    unknown = set(roles) - VALID_TARGET_ROLES
    if unknown:
        raise ValidationRuleError(
            f"Unknown target role(s): {', '.join(sorted(unknown))}.",
            code="invalid_target_role",
        )
    return roles, programs, years


def announcement_matches_viewer(
    *,
    target_roles: Iterable[str],
    target_programs: Iterable[str],
    target_academic_years: Iterable[str],
    viewer_role: str,
    viewer_program: str = "",
    viewer_academic_year: str = "",
) -> bool:
    # BR-DEPT-002: match viewer role, program, and academic year; empty list means all.
    roles = {r.lower() for r in target_roles}
    if "all" not in roles and viewer_role.lower() not in roles:
        return False

    programs = {p.lower() for p in target_programs if p}
    if programs and "all" not in programs and (
        not viewer_program or viewer_program.lower() not in programs
    ):
        return False

    years = {str(y).lower() for y in target_academic_years if str(y)}
    return not (
        years
        and "all" not in years
        and (not viewer_academic_year or str(viewer_academic_year).lower() not in years)
    )


def validate_stock_request(*, requested_quantity: int, current_quantity: int) -> None:
    # BR-DEPT-015: validate positive quantity against current inventory at submission time.
    if requested_quantity <= 0:
        raise ValidationRuleError(
            "Requested quantity must be a positive integer.", code="invalid_quantity"
        )
    if requested_quantity > current_quantity:
        raise InsufficientStock(requested_quantity, current_quantity)


def validate_stock_issuance(*, requested_quantity: int, current_quantity: int) -> int:
    # AFR-DEPT-013: prevent negative balance on concurrent issuance.
    if requested_quantity <= 0:
        raise ValidationRuleError(
            "Issued quantity must be a positive integer.", code="invalid_quantity"
        )
    if requested_quantity > current_quantity:
        raise InsufficientStock(requested_quantity, current_quantity)
    return current_quantity - requested_quantity


def detect_timetable_conflicts(
    existing: Iterable[TimetableSlotSpec], candidate: TimetableSlotSpec
) -> None:
    # BR-DEPT-010: block overlapping slots on room, faculty, or student cohort.
    if candidate.day_of_week < 0 or candidate.day_of_week > 6:
        raise ValidationRuleError("Day of week must be between 0 and 6.", code="invalid_day")
    if candidate.end_time <= candidate.start_time:
        raise ValidationRuleError(
            "End time must be strictly after start time.", code="invalid_time_range"
        )

    for slot in existing:
        if candidate.slot_id is not None and slot.slot_id == candidate.slot_id:
            continue
        if slot.department_id != candidate.department_id:
            continue
        if slot.day_of_week != candidate.day_of_week:
            continue
        overlaps = candidate.start_time < slot.end_time and slot.start_time < candidate.end_time
        if not overlaps:
            continue

        if candidate.room and slot.room and candidate.room.lower() == slot.room.lower():
            raise TimetableConflict(
                f"Room {candidate.room!r} is already booked during that time slot."
            )
        if (
            candidate.faculty_user_id is not None
            and slot.faculty_user_id is not None
            and candidate.faculty_user_id == slot.faculty_user_id
        ):
            raise TimetableConflict("The assigned faculty member already has a slot at that time.")
        if (
            candidate.program
            and slot.program
            and candidate.program.lower() == slot.program.lower()
            and candidate.academic_year == slot.academic_year
            and candidate.section.lower() == slot.section.lower()
        ):
            raise TimetableConflict(
                f"Cohort {candidate.program} ({candidate.academic_year}, {candidate.section}) "
                f"already has a class/lab at that time."
            )


def validate_official_change_field(field_name: str, proposed_value: str) -> str:
    # BR-DEPT-011 / AFR-DEPT-053: Headship cannot be edited via official department change.
    norm = (field_name or "").strip().lower()
    if norm in FORBIDDEN_OFFICIAL_FIELDS:
        raise ForbiddenOfficialField(norm)
    if norm not in EDITABLE_OFFICIAL_FIELDS:
        raise ForbiddenOfficialField(norm)
    if not (proposed_value or "").strip():
        raise ValidationRuleError(
            "Proposed official detail value cannot be empty.", code="empty_proposed_value"
        )
    return norm


def validate_role_tenure(valid_from: datetime, valid_to: datetime) -> None:
    # BR-DEPT-023: every HOD and Dept_Admin assignment must have a bounded interval.
    if valid_from is None or valid_to is None:
        raise InvalidTenure("Both valid_from and valid_to are required for role tenure.")
    if valid_to <= valid_from:
        raise InvalidTenure("valid_to must be strictly later than valid_from.")


def project_profile_fields(
    profile: ProfileSnapshot,
    *,
    viewer_role: str,
    viewer_user_id: int | None,
    is_course_instructor: bool = False,
) -> dict | None:
    # BR-DEPT-019 / AFR-DEPT-025..028: enforce role/relationship visibility without sensitive PII.
    role = viewer_role.lower()
    base = {
        "id": profile.id,
        "department_id": profile.department_id,
        "user_id": profile.user_id,
        "profile_kind": profile.profile_kind,
        "display_name": profile.display_name,
        "program": profile.program,
    }

    if role in ("hod", "dept_admin"):
        # AFR-DEPT-028: full profile excluding sensitive_personal_data.
        return {
            **base,
            "email": profile.email,
            "academic_year": profile.academic_year,
            "designation_title": profile.designation_title,
            "office_room": profile.office_room,
            "research_area": profile.research_area,
            "graduation_year": profile.graduation_year,
            "current_affiliation": profile.current_affiliation,
            "academic_notes": profile.academic_notes,
            "visibility_tier": "full_non_sensitive",
        }

    if role == "faculty":
        if profile.profile_kind == "student":
            # AFR-DEPT-026: detailed view only for students in this faculty member's courses.
            if not is_course_instructor:
                return None
            return {
                **base,
                "email": profile.email,
                "academic_year": profile.academic_year,
                "academic_notes": profile.academic_notes,
                "visibility_tier": "course_student_detailed",
            }
        # AFR-DEPT-027: limited permitted info for Faculty and Alumni.
        return {
            **base,
            "email": profile.email,
            "designation_title": profile.designation_title,
            "office_room": profile.office_room,
            "research_area": profile.research_area,
            "graduation_year": profile.graduation_year,
            "current_affiliation": profile.current_affiliation,
            "visibility_tier": "faculty_limited",
        }

    if role == "student":
        # AFR-DEPT-025: basic permitted peer/Faculty info only; alumni excluded.
        if profile.profile_kind not in ("student", "faculty"):
            return None
        out = {**base, "visibility_tier": "student_basic"}
        if profile.profile_kind == "faculty":
            out["designation_title"] = profile.designation_title
            out["office_room"] = profile.office_room
        elif viewer_user_id is not None and profile.user_id == viewer_user_id:
            out["academic_year"] = profile.academic_year
            out["email"] = profile.email
        return out

    return None
