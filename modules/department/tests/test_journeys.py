from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from conftest import make_session
from modules.department import registry
from modules.department.models import (
    Announcement,
    Department,
    DepartmentNotification,
    DepartmentProfile,
    FeedbackTransition,
    InventoryItem,
    StockMovement,
)
from modules.department.services import roles as role_svc

pytestmark = pytest.mark.django_db


def _client(stub_iam, *, uid: int, role: str, kind: str = "staff"):
    perms = tuple(registry.ROLE_GRANTS[role])
    stub_iam(
        make_session(
            user_id=uid,
            kind=kind,
            roles=(role,),
            active_role=role,
            modules=("department",),
            permissions=perms,
        )
    )
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Token tok")
    return client


@pytest.fixture
def cse():
    return Department.objects.create(
        code="CSE",
        name="Computer Science and Engineering",
        active_hod_user_id=3001,
        active_dept_admin_user_id=4001,
    )


# Ordinary plain student with no optional profile fields (Step 5.2).
def test_plain_student_without_profile_fields_can_browse_safely(stub_iam, cse):
    student = _client(stub_iam, uid=1099, role="student", kind="student")
    assert student.get("/api/v1/department/departments").status_code == 200
    assert student.get("/api/v1/department/announcements").status_code == 200
    assert student.get("/api/v1/department/timetables").status_code == 200
    assert student.get("/api/v1/department/programs").status_code == 200
    assert student.get("/api/v1/department/profiles").status_code == 200


# UC-DEPT-001, UC-DEPT-002, UC-DEPT-003, CFR-DEPT-001..003, AFR-DEPT-001..006, 046.
# BR-DEPT-001, BR-DEPT-002, BR-DEPT-003, BR-DEPT-004, FR-DEPT-001..006, FR-DEPT-046.
def test_uc_dept_001_002_003_announcement_lifecycle(stub_iam, cse):
    DepartmentProfile.objects.create(
        department=cse, user_id=1001, profile_kind="student",
        display_name="Asha", program="BTech", academic_year="2026",
    )
    fac = _client(stub_iam, uid=2001, role="faculty", kind="faculty")
    res = fac.post(
        "/api/v1/department/announcements",
        {
            "department_id": cse.pk,
            "title": "Mid-Sem Viva",
            "content": "Room L-101 at 10 AM.",
            "target_roles": ["student"],
            "target_programs": ["BTech"],
            "target_academic_years": ["2026"],
        },
        format="json",
    )
    assert res.status_code == 201
    ann_id = res.json()["id"]
    assert DepartmentNotification.objects.filter(
        topic="announcement.published", recipient_user_id=1001
    ).exists()

    # UC-DEPT-001: matching student sees it.
    stu = _client(stub_iam, uid=1001, role="student", kind="student")
    rows = stu.get("/api/v1/department/announcements").json()["results"]
    assert [r["id"] for r in rows] == [ann_id]
    assert stu.get(f"/api/v1/department/announcements/{ann_id}").status_code == 200

    # UC-DEPT-003: HOD edits, hides, then deletes.
    hod = _client(stub_iam, uid=3001, role="HOD (CSE)", kind="faculty")
    edit = hod.patch(
        f"/api/v1/department/announcements/{ann_id}",
        {"title": "Mid-Sem Viva (Updated)"},
        format="json",
    )
    assert edit.status_code == 200
    assert edit.json()["title"] == "Mid-Sem Viva (Updated)"

    hide = hod.post(f"/api/v1/department/announcements/{ann_id}/hide", {}, format="json")
    assert hide.status_code == 200
    assert hide.json()["status"] == "hidden"

    # Hidden announcement is no longer visible to student.
    stu = _client(stub_iam, uid=1001, role="student", kind="student")
    assert stu.get("/api/v1/department/announcements").json()["results"] == []

    hod = _client(stub_iam, uid=3001, role="HOD (CSE)", kind="faculty")
    assert hod.delete(f"/api/v1/department/announcements/{ann_id}").status_code == 204
    assert Announcement.objects.get(pk=ann_id).status == "deleted"


# UC-DEPT-019, UC-DEPT-004, UC-DEPT-005, UC-DEPT-006, UC-DEPT-011.
# BW-DEPT-01, BW-DEPT-02, CW-DEPT-01, CFR-DEPT-004..006, AFR-DEPT-007..016, 041..043.
# BR-DEPT-005, BR-DEPT-006, BR-DEPT-007, BR-DEPT-012, BR-DEPT-015, BR-DEPT-016, FR-DEPT-007..016, FR-DEPT-041..043.
def test_uc_dept_004_005_006_011_019_stock_approved_and_rejected_journeys(stub_iam, cse):
    admin = _client(stub_iam, uid=4001, role="deptadmin_cse", kind="staff")
    inv = admin.post(
        "/api/v1/department/inventory",
        {"department_id": cse.pk, "sku": "HDMI-01", "name": "HDMI Cable", "quantity": 10},
        format="json",
    )
    assert inv.status_code == 201
    item_id = inv.json()["id"]
    assert StockMovement.objects.filter(item_id=item_id, movement_type="insertion").count() == 1

    # UC-DEPT-004 alternate flow: insufficient stock blocked (BR-DEPT-015).
    fac = _client(stub_iam, uid=2001, role="faculty", kind="faculty")
    bad = fac.post(
        "/api/v1/department/stock-requests",
        {"item_id": item_id, "requested_quantity": 25},
        format="json",
    )
    assert bad.status_code == 409

    # BW-DEPT-01: Request -> HOD Approve -> Dept_Admin Issue.
    req1 = fac.post(
        "/api/v1/department/stock-requests",
        {"item_id": item_id, "requested_quantity": 4, "purpose": "Lab"},
        format="json",
    )
    assert req1.status_code == 201
    r1_id = req1.json()["id"]
    assert DepartmentNotification.objects.filter(
        topic="stock_request.submitted", recipient_user_id=4001
    ).exists()
    assert DepartmentNotification.objects.filter(
        topic="stock_request.awaiting_hod", recipient_user_id=3001
    ).exists()

    hod = _client(stub_iam, uid=3001, role="HOD (CSE)", kind="faculty")
    dec1 = hod.post(
        f"/api/v1/department/stock-requests/{r1_id}/decide",
        {"approve": True, "note": "Approved"},
        format="json",
    )
    assert dec1.status_code == 200
    assert dec1.json()["status"] == "approved_for_issuance"
    # AFR-DEPT-043: Faculty is NOT notified on intermediate approval.
    assert not DepartmentNotification.objects.filter(
        recipient_user_id=2001, payload__stock_request_id=r1_id
    ).exists()

    admin = _client(stub_iam, uid=4001, role="deptadmin_cse", kind="staff")
    iss1 = admin.post(
        f"/api/v1/department/stock-requests/{r1_id}/issue",
        {"note": "Handed over"},
        format="json",
    )
    assert iss1.status_code == 200
    assert iss1.json()["status"] == "issued"
    assert InventoryItem.objects.get(pk=item_id).current_quantity == 6
    assert StockMovement.objects.filter(item_id=item_id, movement_type="issuance").count() == 1
    assert DepartmentNotification.objects.filter(
        topic="stock_request.issued", recipient_user_id=2001
    ).exists()

    # UC-DEPT-011: Faculty sees issued-stock history.
    fac = _client(stub_iam, uid=2001, role="faculty", kind="faculty")
    movs = fac.get("/api/v1/department/stock-movements").json()["results"]
    assert len(movs) == 1
    assert movs[0]["stock_request_id"] == r1_id

    # BW-DEPT-02: Request -> HOD Reject -> Faculty notified.
    req2 = fac.post(
        "/api/v1/department/stock-requests",
        {"item_id": item_id, "requested_quantity": 2},
        format="json",
    )
    r2_id = req2.json()["id"]
    hod = _client(stub_iam, uid=3001, role="HOD (CSE)", kind="faculty")
    dec2 = hod.post(
        f"/api/v1/department/stock-requests/{r2_id}/decide",
        {"approve": False, "note": "Not needed"},
        format="json",
    )
    assert dec2.status_code == 200
    assert dec2.json()["status"] == "rejected"
    assert DepartmentNotification.objects.filter(
        topic="stock_request.rejected", recipient_user_id=2001
    ).exists()


# UC-DEPT-007, UC-DEPT-008, UC-DEPT-014, BW-DEPT-03, BW-DEPT-04, CW-DEPT-02.
# CFR-DEPT-007, CFR-DEPT-008, AFR-DEPT-017..023, 044, 045, FR-DEPT-017..023, FR-DEPT-044, FR-DEPT-045.
# BR-DEPT-008, BR-DEPT-009, BR-DEPT-017, BR-DEPT-018.
def test_uc_dept_007_008_014_feedback_journeys(stub_iam, cse):
    stu = _client(stub_iam, uid=1001, role="student", kind="student")
    fb1 = stu.post(
        "/api/v1/department/feedback",
        {"department_id": cse.pk, "subject": "WiFi", "body": "Weak signal in L-204."},
        format="json",
    )
    assert fb1.status_code == 201
    fb1_id = fb1.json()["id"]
    assert DepartmentNotification.objects.filter(
        topic="feedback.submitted", recipient_user_id=4001
    ).exists()

    # BW-DEPT-04: Dept_Admin initial review -> HOD oversight & resolution.
    admin = _client(stub_iam, uid=4001, role="deptadmin_cse", kind="staff")
    rev1 = admin.post(
        f"/api/v1/department/feedback/{fb1_id}/review",
        {"category": "Network", "close_as_simple": False, "note": "Categorized"},
        format="json",
    )
    assert rev1.status_code == 200
    assert rev1.json()["status"] == "under_review"

    hod = _client(stub_iam, uid=3001, role="HOD (CSE)", kind="faculty")
    disp1 = hod.post(
        f"/api/v1/department/feedback/{fb1_id}/dispose",
        {"status": "resolved", "note": "AP replaced."},
        format="json",
    )
    assert disp1.status_code == 200
    assert disp1.json()["status"] == "resolved"
    assert FeedbackTransition.objects.filter(feedback_id=fb1_id).count() == 2
    assert DepartmentNotification.objects.filter(
        topic="feedback.resolved", recipient_user_id=1001
    ).exists()

    # BW-DEPT-03: Dept_Admin closes simple issue during initial review (AFR-DEPT-021).
    stu = _client(stub_iam, uid=1001, role="student", kind="student")
    fb2_id = stu.post(
        "/api/v1/department/feedback",
        {"department_id": cse.pk, "subject": "Chalk", "body": "Need chalk in L-101."},
        format="json",
    ).json()["id"]
    admin = _client(stub_iam, uid=4001, role="deptadmin_cse", kind="staff")
    rev2 = admin.post(
        f"/api/v1/department/feedback/{fb2_id}/review",
        {"category": "Supplies", "close_as_simple": True, "note": "Restocked."},
        format="json",
    )
    assert rev2.status_code == 200
    assert rev2.json()["status"] == "closed"
    assert DepartmentNotification.objects.filter(
        topic="feedback.closed", recipient_user_id=1001
    ).exists()


# UC-DEPT-009, UC-DEPT-017, UC-DEPT-018, UC-DEPT-011, CFR-DEPT-011..013.
# AFR-DEPT-029..031, 034..037, FR-DEPT-029..031, FR-DEPT-034..037, BR-DEPT-010, BR-DEPT-012.
def test_uc_dept_009_017_018_timetable_labs_and_programs(stub_iam, cse):
    admin = _client(stub_iam, uid=4001, role="deptadmin_cse", kind="staff")
    slot1 = admin.post(
        "/api/v1/department/timetables",
        {
            "department_id": cse.pk, "slot_kind": "class", "program": "BTech",
            "academic_year": "2026-27", "section": "A", "course_code": "CS201",
            "course_title": "DSA", "faculty_user_id": 2001, "room": "L-101",
            "day_of_week": 1, "start_time": "09:00:00", "end_time": "10:00:00",
        },
        format="json",
    )
    assert slot1.status_code == 201
    slot_id = slot1.json()["id"]

    # BR-DEPT-010: overlapping room blocked with 409.
    conflict = admin.post(
        "/api/v1/department/timetables",
        {
            "department_id": cse.pk, "slot_kind": "lab", "program": "MTech",
            "academic_year": "2026-27", "section": "B", "course_code": "CS501",
            "course_title": "ML Lab", "faculty_user_id": 2002, "room": "L-101",
            "day_of_week": 1, "start_time": "09:30:00", "end_time": "10:30:00",
        },
        format="json",
    )
    assert conflict.status_code == 409

    # Modify existing slot cleanly.
    upd = admin.patch(f"/api/v1/department/timetables/{slot_id}", {"room": "L-102"}, format="json")
    assert upd.status_code == 200
    assert upd.json()["room"] == "L-102"

    # UC-DEPT-017: Lab management + UC-DEPT-011 Faculty view.
    lab = admin.post(
        "/api/v1/department/labs",
        {"department_id": cse.pk, "lab_code": "ML-1", "name": "ML Lab", "capacity": 30},
        format="json",
    )
    assert lab.status_code == 201
    lab_id = lab.json()["id"]
    assert admin.patch(
        f"/api/v1/department/labs/{lab_id}", {"name": "ML & AI Lab", "capacity": 40}, format="json"
    ).status_code == 200

    fac = _client(stub_iam, uid=2001, role="faculty", kind="faculty")
    assert len(fac.get("/api/v1/department/labs").json()["results"]) == 1

    # UC-DEPT-018: Program management + Student view of programs and timetables.
    admin = _client(stub_iam, uid=4001, role="deptadmin_cse", kind="staff")
    prog = admin.post(
        "/api/v1/department/programs",
        {"department_id": cse.pk, "code": "BTECH-CSE", "name": "B.Tech CSE", "degree_level": "UG"},
        format="json",
    )
    assert prog.status_code == 201
    prog_id = prog.json()["id"]
    assert admin.patch(
        f"/api/v1/department/programs/{prog_id}", {"name": "B.Tech CSE (Hons)"}, format="json"
    ).status_code == 200

    stu = _client(stub_iam, uid=1001, role="student", kind="student")
    assert len(stu.get("/api/v1/department/programs").json()["results"]) == 1
    assert len(stu.get("/api/v1/department/timetables").json()["results"]) == 1


# UC-DEPT-010, UC-DEPT-012, BW-DEPT-05, BW-DEPT-06, CW-DEPT-03.
# CFR-DEPT-014, CFR-DEPT-015, AFR-DEPT-038..040, FR-DEPT-038..040, BR-DEPT-011, BR-DEPT-013.
def test_uc_dept_010_012_department_details_and_official_changes(stub_iam, cse):
    admin = _client(stub_iam, uid=4001, role="deptadmin_cse", kind="staff")
    gen = admin.patch(
        f"/api/v1/department/departments/{cse.pk}",
        {"description": "Updated general description", "location": "Block C"},
        format="json",
    )
    assert gen.status_code == 200
    assert gen.json()["description"] == "Updated general description"

    # BW-DEPT-05: Propose official change -> pending -> HOD approves -> effective.
    p1 = admin.post(
        "/api/v1/department/official-changes",
        {"department_id": cse.pk, "field_name": "core_policies", "proposed_value": "Policy v2"},
        format="json",
    )
    assert p1.status_code == 201
    c1_id = p1.json()["id"]
    cse.refresh_from_db()
    assert cse.core_policies == ""

    hod = _client(stub_iam, uid=3001, role="HOD (CSE)", kind="faculty")
    d1 = hod.post(
        f"/api/v1/department/official-changes/{c1_id}/decide",
        {"approve": True, "note": "Adopted"},
        format="json",
    )
    assert d1.status_code == 200
    assert d1.json()["status"] == "approved"
    cse.refresh_from_db()
    assert cse.core_policies == "Policy v2"

    # BW-DEPT-06: Propose official change -> HOD rejects -> current data retained.
    admin = _client(stub_iam, uid=4001, role="deptadmin_cse", kind="staff")
    c2_id = admin.post(
        "/api/v1/department/official-changes",
        {"department_id": cse.pk, "field_name": "name", "proposed_value": "Wrong Name"},
        format="json",
    ).json()["id"]
    hod = _client(stub_iam, uid=3001, role="HOD (CSE)", kind="faculty")
    d2 = hod.post(
        f"/api/v1/department/official-changes/{c2_id}/decide",
        {"approve": False, "note": "Keep current name"},
        format="json",
    )
    assert d2.status_code == 200
    assert d2.json()["status"] == "rejected"
    cse.refresh_from_db()
    assert cse.name == "Computer Science and Engineering"


# UC-DEPT-015, UC-DEPT-016, CFR-DEPT-009, CFR-DEPT-010, AFR-DEPT-024..028, FR-DEPT-024..028, BR-DEPT-019.
def test_uc_dept_015_016_profile_management_and_visibility(stub_iam, cse):
    admin = _client(stub_iam, uid=4001, role="deptadmin_cse", kind="staff")
    p_stu = admin.post(
        "/api/v1/department/profiles",
        {
            "department_id": cse.pk, "user_id": 1001, "profile_kind": "student",
            "display_name": "Asha Verma", "email": "asha@inst.ac.in",
            "program": "BTech", "academic_year": "2026", "academic_notes": "Top 5%",
        },
        format="json",
    )
    assert p_stu.status_code == 201
    stu_prof_id = p_stu.json()["id"]

    # Register course enrollment so Faculty 2001 can see detailed student profile.
    enr = admin.post(
        "/api/v1/department/roster",
        {
            "department_id": cse.pk, "course_code": "CS201",
            "faculty_user_id": 2001, "student_user_id": 1001,
        },
        format="json",
    )
    assert enr.status_code == 201

    fac = _client(stub_iam, uid=2001, role="faculty", kind="faculty")
    detail = fac.get(f"/api/v1/department/profiles/{stu_prof_id}")
    assert detail.status_code == 200
    assert detail.json()["academic_notes"] == "Top 5%"


# UC-DEPT-020, UC-DEPT-022, BW-DEPT-07, BW-DEPT-08, CW-DEPT-04.
# CFR-DEPT-016, AFR-DEPT-047..053, FR-DEPT-047..053, BR-DEPT-021..024.
def test_uc_dept_020_022_role_assignment_and_effective_transition(stub_iam, cse):
    inst_admin = _client(stub_iam, uid=9001, role="acadadmin", kind="staff")
    now = timezone.now()

    # Immediate HOD assignment activates and syncs Headship (BW-DEPT-07, AFR-DEPT-053).
    r1 = inst_admin.post(
        "/api/v1/department/role-assignments",
        {
            "department_id": cse.pk, "role_type": "hod", "user_id": 3010,
            "valid_from": (now - timedelta(hours=1)).isoformat(),
            "valid_to": (now + timedelta(days=365)).isoformat(),
        },
        format="json",
    )
    assert r1.status_code == 201
    assert r1.json()["status"] == "active"
    cse.refresh_from_db()
    assert cse.active_hod_user_id == 3010

    # Scheduled future HOD reassignment transitions when effective time arrives (UC-DEPT-022).
    future_from = now + timedelta(days=10)
    r2 = inst_admin.post(
        "/api/v1/department/role-assignments",
        {
            "department_id": cse.pk, "role_type": "hod", "user_id": 3020,
            "valid_from": future_from.isoformat(),
            "valid_to": (now + timedelta(days=400)).isoformat(),
        },
        format="json",
    )
    assert r2.status_code == 201
    assert r2.json()["status"] == "scheduled"

    changed = role_svc.apply_effective_transitions(now=future_from + timedelta(seconds=1))
    assert changed == 1
    cse.refresh_from_db()
    assert cse.active_hod_user_id == 3020

    # BW-DEPT-08: Dept_Admin reassignment transitions cleanly.
    da = inst_admin.post(
        "/api/v1/department/role-assignments",
        {
            "department_id": cse.pk, "role_type": "dept_admin", "user_id": 4010,
            "valid_from": (now - timedelta(minutes=5)).isoformat(),
            "valid_to": (now + timedelta(days=180)).isoformat(),
        },
        format="json",
    )
    assert da.status_code == 201
    assert da.json()["status"] == "active"
    cse.refresh_from_db()
    assert cse.active_dept_admin_user_id == 4010
