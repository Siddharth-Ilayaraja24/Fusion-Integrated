from datetime import UTC, datetime, time

import pytest

from modules.department.domain import errors, rules
from modules.department.domain import state_machine as sm


# -- State Machine Exhaustive Tests (CW-DEPT-01..04, BW-DEPT-01..08) ----------
@pytest.mark.parametrize(
    ("entity", "states", "terminal", "transitions"),
    [
        (
            "stock_request",
            (sm.STOCK_PENDING, sm.STOCK_APPROVED, sm.STOCK_REJECTED, sm.STOCK_ISSUED),
            sm.STOCK_TERMINAL,
            sm.STOCK_TRANSITIONS,
        ),
        (
            "feedback",
            (sm.FEEDBACK_NEW, sm.FEEDBACK_UNDER_REVIEW, sm.FEEDBACK_RESOLVED, sm.FEEDBACK_CLOSED),
            sm.FEEDBACK_TERMINAL,
            sm.FEEDBACK_TRANSITIONS,
        ),
        (
            "official_change",
            (sm.OFFICIAL_PENDING, sm.OFFICIAL_APPROVED, sm.OFFICIAL_REJECTED),
            sm.OFFICIAL_TERMINAL,
            sm.OFFICIAL_CHANGE_TRANSITIONS,
        ),
        (
            "role_assignment",
            (
                sm.ROLE_SCHEDULED,
                sm.ROLE_ACTIVE,
                sm.ROLE_SUPERSEDED,
                sm.ROLE_EXPIRED,
                sm.ROLE_CANCELLED,
            ),
            sm.ROLE_TERMINAL,
            sm.ROLE_ASSIGNMENT_TRANSITIONS,
        ),
    ],
)
def test_transition_matrix_matches_table_and_terminal_states_have_no_exits(
    entity, states, terminal, transitions
):
    legal_pairs = {(t.frm, t.to): t for t in transitions}
    for frm in states:
        for to in states:
            if (frm, to) in legal_pairs:
                assert sm.is_legal(entity, frm, to) is True
                t = legal_pairs[(frm, to)]
                for actor in t.actors:
                    assert sm.resolve(entity, frm, to, actor) == t
                for wrong_actor in (
                    sm.ACTOR_STUDENT,
                    sm.ACTOR_FACULTY,
                    sm.ACTOR_DEPT_ADMIN,
                    sm.ACTOR_HOD,
                    sm.ACTOR_INSTITUTE_ADMIN,
                    sm.ACTOR_SYSTEM,
                ):
                    if wrong_actor not in t.actors:
                        with pytest.raises(errors.ActorNotAllowed):
                            sm.resolve(entity, frm, to, wrong_actor)
            else:
                assert sm.is_legal(entity, frm, to) is False
                with pytest.raises(errors.InvalidTransition):
                    sm.resolve(entity, frm, to)
        if frm in terminal:
            assert sm.allowed_targets(entity, frm) == []


def test_allowed_targets_filtered_by_actor():
    assert sm.allowed_targets("stock_request", sm.STOCK_PENDING, sm.ACTOR_HOD) == [
        sm.STOCK_APPROVED,
        sm.STOCK_REJECTED,
    ]
    assert sm.allowed_targets("stock_request", sm.STOCK_PENDING, sm.ACTOR_DEPT_ADMIN) == []
    assert sm.allowed_targets("feedback", sm.FEEDBACK_NEW, sm.ACTOR_HOD) == []
    assert sm.allowed_targets("feedback", sm.FEEDBACK_UNDER_REVIEW, sm.ACTOR_HOD) == [
        sm.FEEDBACK_CLOSED,
        sm.FEEDBACK_RESOLVED,
    ]


# -- Announcement Rules (BR-DEPT-002, BR-DEPT-003) ----------------------------
def test_announcement_validation_br_dept_003():
    roles, progs, years = rules.validate_announcement_payload(
        title="Exam",
        content="Starts Monday",
        target_roles=["Student", "faculty"],
        target_programs=["BTech"],
        target_academic_years=["2026"],
    )
    assert roles == ["faculty", "student"]
    assert progs == ["BTech"]
    assert years == ["2026"]

    with pytest.raises(errors.ValidationRuleError):
        rules.validate_announcement_payload(
            title="", content="x", target_roles=["student"],
            target_programs=[], target_academic_years=[],
        )
    with pytest.raises(errors.ValidationRuleError):
        rules.validate_announcement_payload(
            title="t", content="  ", target_roles=["student"],
            target_programs=[], target_academic_years=[],
        )
    with pytest.raises(errors.ValidationRuleError):
        rules.validate_announcement_payload(
            title="t", content="c", target_roles=[],
            target_programs=[], target_academic_years=[],
        )
    with pytest.raises(errors.ValidationRuleError):
        rules.validate_announcement_payload(
            title="t", content="c", target_roles=["unknown_role"],
            target_programs=[], target_academic_years=[],
        )


def test_announcement_matching_br_dept_002():
    assert rules.announcement_matches_viewer(
        target_roles=["all"], target_programs=[], target_academic_years=[],
        viewer_role="student",
    )
    assert not rules.announcement_matches_viewer(
        target_roles=["faculty"], target_programs=[], target_academic_years=[],
        viewer_role="student",
    )
    assert not rules.announcement_matches_viewer(
        target_roles=["student"], target_programs=["MTech"], target_academic_years=[],
        viewer_role="student", viewer_program="BTech",
    )
    assert rules.announcement_matches_viewer(
        target_roles=["student"], target_programs=["BTech"], target_academic_years=["2026"],
        viewer_role="student", viewer_program="btech", viewer_academic_year="2026",
    )
    assert not rules.announcement_matches_viewer(
        target_roles=["student"], target_programs=["BTech"], target_academic_years=["2026"],
        viewer_role="student", viewer_program="BTech", viewer_academic_year="2025",
    )


# -- Stock Rules (BR-DEPT-015, AFR-DEPT-013) ----------------------------------
def test_stock_request_and_issuance_validation_br_dept_015():
    rules.validate_stock_request(requested_quantity=5, current_quantity=5)
    with pytest.raises(errors.ValidationRuleError):
        rules.validate_stock_request(requested_quantity=0, current_quantity=5)
    with pytest.raises(errors.InsufficientStock):
        rules.validate_stock_request(requested_quantity=6, current_quantity=5)

    assert rules.validate_stock_issuance(requested_quantity=3, current_quantity=5) == 2
    with pytest.raises(errors.ValidationRuleError):
        rules.validate_stock_issuance(requested_quantity=0, current_quantity=5)
    with pytest.raises(errors.InsufficientStock):
        rules.validate_stock_issuance(requested_quantity=6, current_quantity=5)


# -- Timetable Conflict Detection (BR-DEPT-010) -------------------------------
def _slot(**kw):
    base = {
        "slot_id": 1, "department_id": 1, "day_of_week": 1,
        "start_time": time(9, 0), "end_time": time(10, 0),
        "room": "L-101", "faculty_user_id": 2001,
        "program": "BTech", "academic_year": "2026-27", "section": "A",
    }
    base.update(kw)
    return rules.TimetableSlotSpec(**base)


def test_timetable_conflicts_br_dept_010():
    existing = [_slot()]
    # Adjacent non-overlapping slot is allowed.
    rules.detect_timetable_conflicts(
        existing, _slot(slot_id=None, start_time=time(10, 0), end_time=time(11, 0))
    )
    # Editing the same slot does not conflict with itself.
    rules.detect_timetable_conflicts(existing, _slot(slot_id=1))
    # Different department or day does not conflict.
    rules.detect_timetable_conflicts(existing, _slot(slot_id=None, department_id=2))
    rules.detect_timetable_conflicts(existing, _slot(slot_id=None, day_of_week=2))

    # Room conflict.
    with pytest.raises(errors.TimetableConflict):
        rules.detect_timetable_conflicts(
            existing,
            _slot(slot_id=None, faculty_user_id=2002, section="B",
                  start_time=time(9, 30), end_time=time(10, 30)),
        )
    # Faculty conflict.
    with pytest.raises(errors.TimetableConflict):
        rules.detect_timetable_conflicts(
            existing, _slot(slot_id=None, room="L-102", section="B")
        )
    # Cohort conflict.
    with pytest.raises(errors.TimetableConflict):
        rules.detect_timetable_conflicts(
            existing, _slot(slot_id=None, room="L-102", faculty_user_id=2002)
        )
    # Invalid day / time range.
    with pytest.raises(errors.ValidationRuleError):
        rules.detect_timetable_conflicts(existing, _slot(slot_id=None, day_of_week=7))
    with pytest.raises(errors.ValidationRuleError):
        rules.detect_timetable_conflicts(
            existing, _slot(slot_id=None, start_time=time(10, 0), end_time=time(9, 0))
        )


# -- Official Change & Role Tenure (BR-DEPT-011, BR-DEPT-023, AFR-DEPT-053) ---
def test_official_change_field_and_tenure_rules():
    assert rules.validate_official_change_field("name", "CSE Dept") == "name"
    assert rules.validate_official_change_field("core_policies", "Policy v2") == "core_policies"
    for forbidden in ("headship", "hod", "active_hod_user_id", "unknown_field"):
        with pytest.raises(errors.ForbiddenOfficialField):
            rules.validate_official_change_field(forbidden, "x")
    with pytest.raises(errors.ValidationRuleError):
        rules.validate_official_change_field("name", "   ")

    t1 = datetime(2026, 8, 1, tzinfo=UTC)
    t2 = datetime(2027, 8, 1, tzinfo=UTC)
    rules.validate_role_tenure(t1, t2)
    with pytest.raises(errors.InvalidTenure):
        rules.validate_role_tenure(t2, t1)
    with pytest.raises(errors.InvalidTenure):
        rules.validate_role_tenure(None, t2)


# -- Profile Visibility Matrix (BR-DEPT-019, AFR-DEPT-025..028) ---------------
def test_profile_visibility_matrix_br_dept_019():
    student = rules.ProfileSnapshot(
        id=1, department_id=1, user_id=1001, profile_kind="student",
        display_name="Asha", email="asha@inst.ac.in", program="BTech",
        academic_year="2026", designation_title="", office_room="",
        research_area="", graduation_year=None, current_affiliation="",
        academic_notes="Dean's list",
    )
    faculty = rules.ProfileSnapshot(
        id=2, department_id=1, user_id=2001, profile_kind="faculty",
        display_name="Dr. Rao", email="rao@inst.ac.in", program="",
        academic_year="", designation_title="Professor", office_room="C-201",
        research_area="Systems", graduation_year=None, current_affiliation="",
        academic_notes="",
    )
    alumni = rules.ProfileSnapshot(
        id=3, department_id=1, user_id=3001, profile_kind="alumni",
        display_name="Meera", email="meera@alumni.org", program="BTech",
        academic_year="", designation_title="", office_room="",
        research_area="", graduation_year=2022, current_affiliation="Acme",
        academic_notes="",
    )

    # Student viewing peer, self, faculty, alumni (AFR-DEPT-025).
    peer_view = rules.project_profile_fields(student, viewer_role="student", viewer_user_id=1002)
    assert peer_view["visibility_tier"] == "student_basic"
    assert "academic_notes" not in peer_view and "email" not in peer_view
    self_view = rules.project_profile_fields(student, viewer_role="student", viewer_user_id=1001)
    assert self_view["email"] == "asha@inst.ac.in"
    fac_view = rules.project_profile_fields(faculty, viewer_role="student", viewer_user_id=1002)
    assert fac_view["designation_title"] == "Professor"
    assert rules.project_profile_fields(alumni, viewer_role="student", viewer_user_id=1002) is None

    # Faculty viewing enrolled vs unenrolled student & alumni (AFR-DEPT-026, AFR-DEPT-027).
    assert (
        rules.project_profile_fields(
            student, viewer_role="faculty", viewer_user_id=2001, is_course_instructor=False
        )
        is None
    )
    enrolled = rules.project_profile_fields(
        student, viewer_role="faculty", viewer_user_id=2001, is_course_instructor=True
    )
    assert enrolled["academic_notes"] == "Dean's list"
    alumni_fac = rules.project_profile_fields(alumni, viewer_role="faculty", viewer_user_id=2001)
    assert alumni_fac["current_affiliation"] == "Acme"

    # HOD/Dept_Admin full non-sensitive view (AFR-DEPT-028).
    hod_view = rules.project_profile_fields(student, viewer_role="hod", viewer_user_id=9001)
    assert hod_view["visibility_tier"] == "full_non_sensitive"
    assert "sensitive_personal_data" not in hod_view
    assert rules.project_profile_fields(student, viewer_role="other", viewer_user_id=9999) is None
