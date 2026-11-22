from __future__ import annotations

from datetime import time

from django.db import IntegrityError, transaction

from core.api.exceptions import BadRequestError, ConflictError, NotFoundError
from modules.department.domain import errors as domain_errors
from modules.department.domain import rules
from modules.department.models import DepartmentProgram, LabResource, TimetableSlot
from modules.department.selectors.scoping import lab_resources_for, programs_for, timetables_for
from modules.department.services.authz import require, require_department


def _slot_spec(slot: TimetableSlot) -> rules.TimetableSlotSpec:
    return rules.TimetableSlotSpec(
        slot_id=slot.pk,
        department_id=slot.department_id,
        day_of_week=slot.day_of_week,
        start_time=slot.start_time,
        end_time=slot.end_time,
        room=slot.room,
        faculty_user_id=slot.faculty_user_id,
        program=slot.program,
        academic_year=slot.academic_year,
        section=slot.section,
    )


@transaction.atomic
def create_timetable_slot(
    *,
    department_id: int,
    actor,
    slot_kind: str,
    program: str,
    academic_year: str,
    section: str,
    course_code: str,
    course_title: str,
    room: str,
    day_of_week: int,
    start_time: time,
    end_time: time,
    faculty_user_id: int | None = None,
) -> TimetableSlot:
    # UC-DEPT-009 / BR-DEPT-010 / AFR-DEPT-029 / AFR-DEPT-031.
    require(actor, "department.timetable.create")
    dept = require_department(actor, department_id)

    # Lock the department's active slots for that day to prevent concurrent overlap races.
    existing = list(
        TimetableSlot.objects.select_for_update().filter(
            department=dept, day_of_week=day_of_week, is_active=True
        )
    )
    candidate = rules.TimetableSlotSpec(
        slot_id=None,
        department_id=dept.pk,
        day_of_week=day_of_week,
        start_time=start_time,
        end_time=end_time,
        room=room.strip(),
        faculty_user_id=faculty_user_id,
        program=program.strip(),
        academic_year=academic_year.strip(),
        section=(section or "A").strip(),
    )
    try:
        rules.detect_timetable_conflicts([_slot_spec(s) for s in existing], candidate)
    except domain_errors.TimetableConflict as exc:
        raise ConflictError(exc.message, code=exc.code) from exc
    except domain_errors.ValidationRuleError as exc:
        raise BadRequestError(exc.message, code=exc.code) from exc

    return TimetableSlot.objects.create(
        department=dept,
        slot_kind=slot_kind,
        program=candidate.program,
        academic_year=candidate.academic_year,
        section=candidate.section,
        course_code=course_code.strip().upper(),
        course_title=course_title.strip(),
        faculty_user_id=faculty_user_id,
        room=candidate.room,
        day_of_week=day_of_week,
        start_time=start_time,
        end_time=end_time,
        updated_by_user_id=actor.user_id,
    )


@transaction.atomic
def update_timetable_slot(*, slot_id: int, actor, **changes) -> TimetableSlot:
    # UC-DEPT-009 / BR-DEPT-010 / AFR-DEPT-030 / AFR-DEPT-031.
    require(actor, "department.timetable.update")
    slot = timetables_for(actor).select_for_update().filter(pk=slot_id).first()
    if slot is None:
        raise NotFoundError("Timetable slot not found.", code="timetable_slot_not_found")

    day = changes.get("day_of_week", slot.day_of_week)
    start = changes.get("start_time", slot.start_time)
    end = changes.get("end_time", slot.end_time)
    room = (changes.get("room", slot.room) or "").strip()
    faculty_id = changes.get("faculty_user_id", slot.faculty_user_id)
    program = (changes.get("program", slot.program) or "").strip()
    academic_year = (changes.get("academic_year", slot.academic_year) or "").strip()
    section = (changes.get("section", slot.section) or "A").strip()

    existing = list(
        TimetableSlot.objects.select_for_update().filter(
            department_id=slot.department_id, day_of_week=day, is_active=True
        )
    )
    candidate = rules.TimetableSlotSpec(
        slot_id=slot.pk,
        department_id=slot.department_id,
        day_of_week=day,
        start_time=start,
        end_time=end,
        room=room,
        faculty_user_id=faculty_id,
        program=program,
        academic_year=academic_year,
        section=section,
    )
    try:
        rules.detect_timetable_conflicts([_slot_spec(s) for s in existing], candidate)
    except domain_errors.TimetableConflict as exc:
        raise ConflictError(exc.message, code=exc.code) from exc
    except domain_errors.ValidationRuleError as exc:
        raise BadRequestError(exc.message, code=exc.code) from exc

    for field in ("slot_kind", "course_code", "course_title", "is_active"):
        if field in changes:
            setattr(slot, field, changes[field])
    slot.day_of_week = day
    slot.start_time = start
    slot.end_time = end
    slot.room = room
    slot.faculty_user_id = faculty_id
    slot.program = program
    slot.academic_year = academic_year
    slot.section = section
    slot.updated_by_user_id = actor.user_id
    slot.save()
    return slot


@transaction.atomic
def create_or_update_lab(
    *,
    actor,
    lab_id: int | None = None,
    department_id: int | None = None,
    lab_code: str = "",
    name: str = "",
    location: str = "",
    equipment_summary: str = "",
    capacity: int = 0,
    status: str = "operational",
    incharge_user_id: int | None = None,
) -> LabResource:
    # UC-DEPT-017 / AFR-DEPT-034.
    require(actor, "department.lab.update")
    if lab_id is not None:
        lab = lab_resources_for(actor).select_for_update().filter(pk=lab_id).first()
        if lab is None:
            raise NotFoundError("Lab resource not found.", code="lab_not_found")
        if name:
            lab.name = name.strip()
        if location is not None:
            lab.location = location.strip()
        if equipment_summary is not None:
            lab.equipment_summary = equipment_summary.strip()
        lab.capacity = capacity
        lab.status = status
        lab.incharge_user_id = incharge_user_id
        lab.updated_by_user_id = actor.user_id
        lab.save()
        return lab

    if department_id is None:
        raise BadRequestError("department_id is required.", code="missing_department")
    dept = require_department(actor, department_id)
    clean_code = (lab_code or "").strip().upper()
    if not clean_code or not (name or "").strip():
        raise BadRequestError("lab_code and name are required.", code="missing_lab_fields")
    try:
        return LabResource.objects.create(
            department=dept,
            lab_code=clean_code,
            name=name.strip(),
            location=(location or "").strip(),
            equipment_summary=(equipment_summary or "").strip(),
            capacity=capacity,
            status=status,
            incharge_user_id=incharge_user_id,
            updated_by_user_id=actor.user_id,
        )
    except IntegrityError as exc:
        raise ConflictError(
            f"Lab code {clean_code!r} already exists in this department.",
            code="duplicate_lab_code",
        ) from exc


@transaction.atomic
def create_or_update_program(
    *,
    actor,
    program_id: int | None = None,
    department_id: int | None = None,
    code: str = "",
    name: str = "",
    degree_level: str = "",
    duration_years: int = 4,
    description: str = "",
    is_active: bool = True,
) -> DepartmentProgram:
    # UC-DEPT-018 / AFR-DEPT-036.
    require(actor, "department.program.update")
    if program_id is not None:
        prog = programs_for(actor).select_for_update().filter(pk=program_id).first()
        if prog is None:
            raise NotFoundError("Academic program not found.", code="program_not_found")
        if name:
            prog.name = name.strip()
        if degree_level:
            prog.degree_level = degree_level.strip()
        prog.duration_years = duration_years
        prog.description = (description or "").strip()
        prog.is_active = is_active
        prog.save()
        return prog

    if department_id is None:
        raise BadRequestError("department_id is required.", code="missing_department")
    dept = require_department(actor, department_id)
    clean_code = (code or "").strip().upper()
    if not clean_code or not (name or "").strip():
        raise BadRequestError("Program code and name are required.", code="missing_program_fields")
    try:
        return DepartmentProgram.objects.create(
            department=dept,
            code=clean_code,
            name=name.strip(),
            degree_level=(degree_level or "UG").strip(),
            duration_years=duration_years,
            description=(description or "").strip(),
            is_active=is_active,
        )
    except IntegrityError as exc:
        raise ConflictError(
            f"Program code {clean_code!r} already exists in this department.",
            code="duplicate_program_code",
        ) from exc
