from __future__ import annotations

from django.db import IntegrityError, transaction

from core.api.exceptions import BadRequestError, ConflictError, NotFoundError
from modules.department.models import CourseEnrollment, DepartmentProfile
from modules.department.selectors.scoping import scoped_department_codes
from modules.department.services.authz import require, require_department


@transaction.atomic
def upsert_profile(
    *,
    actor,
    profile_id: int | None = None,
    department_id: int | None = None,
    user_id: int | None = None,
    profile_kind: str = "student",
    display_name: str = "",
    email: str = "",
    program: str = "",
    academic_year: str = "",
    designation_title: str = "",
    office_room: str = "",
    research_area: str = "",
    graduation_year: int | None = None,
    current_affiliation: str = "",
    academic_notes: str = "",
) -> DepartmentProfile:
    # UC-DEPT-016 / AFR-DEPT-024: Dept_Admin manages Faculty, Student, and Alumni profiles.
    require(actor, "department.profile.update")
    if profile_id is not None:
        qs = DepartmentProfile.objects.select_for_update()
        codes = scoped_department_codes(actor)
        if codes is not None:
            qs = qs.filter(department__code__in=codes)
        prof = qs.filter(pk=profile_id).first()
        if prof is None:
            raise NotFoundError("Department profile not found.", code="profile_not_found")
        if display_name:
            prof.display_name = display_name.strip()
        prof.email = (email or "").strip()
        prof.program = (program or "").strip()
        prof.academic_year = (academic_year or "").strip()
        prof.designation_title = (designation_title or "").strip()
        prof.office_room = (office_room or "").strip()
        prof.research_area = (research_area or "").strip()
        prof.graduation_year = graduation_year
        prof.current_affiliation = (current_affiliation or "").strip()
        prof.academic_notes = (academic_notes or "").strip()
        prof.save()
        return prof

    if department_id is None or user_id is None:
        raise BadRequestError(
            "department_id and user_id are required.", code="missing_profile_keys"
        )
    dept = require_department(actor, department_id)
    if not (display_name or "").strip():
        raise BadRequestError("display_name is required.", code="missing_display_name")
    try:
        return DepartmentProfile.objects.create(
            department=dept,
            user_id=user_id,
            profile_kind=profile_kind,
            display_name=display_name.strip(),
            email=(email or "").strip(),
            program=(program or "").strip(),
            academic_year=(academic_year or "").strip(),
            designation_title=(designation_title or "").strip(),
            office_room=(office_room or "").strip(),
            research_area=(research_area or "").strip(),
            graduation_year=graduation_year,
            current_affiliation=(current_affiliation or "").strip(),
            academic_notes=(academic_notes or "").strip(),
        )
    except IntegrityError as exc:
        raise ConflictError(
            "A profile for this user already exists in the department.",
            code="duplicate_profile",
        ) from exc


@transaction.atomic
def add_course_enrollment(
    *,
    department_id: int,
    actor,
    course_code: str,
    faculty_user_id: int,
    student_user_id: int,
    academic_year: str = "",
) -> CourseEnrollment:
    # AFR-DEPT-026 / BR-DEPT-019: register Faculty-Student course link for profile visibility.
    require(actor, "department.roster.update")
    dept = require_department(actor, department_id)
    clean_code = (course_code or "").strip().upper()
    if not clean_code:
        raise BadRequestError("course_code is required.", code="missing_course_code")
    if faculty_user_id == student_user_id:
        raise BadRequestError(
            "Faculty and student cannot be the same user.", code="invalid_enrollment"
        )
    obj, _ = CourseEnrollment.objects.get_or_create(
        department=dept,
        course_code=clean_code,
        faculty_user_id=faculty_user_id,
        student_user_id=student_user_id,
        defaults={"academic_year": (academic_year or "").strip()},
    )
    return obj
