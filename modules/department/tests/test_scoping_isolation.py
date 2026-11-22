import pytest
from rest_framework.test import APIClient

from conftest import make_session
from modules.department import registry
from modules.department.models import (
    Announcement,
    CourseEnrollment,
    Department,
    DepartmentProfile,
    Feedback,
    InventoryItem,
    StockMovement,
    StockRequest,
)

pytestmark = pytest.mark.django_db


def _as(stub_iam, *, uid: int, role: str, kind: str = "staff"):
    stub_iam(
        make_session(
            user_id=uid, kind=kind, roles=(role,), active_role=role,
            modules=("department",), permissions=tuple(registry.ROLE_GRANTS[role]),
        )
    )
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Token tok")
    return client


@pytest.fixture
def two_depts():
    cse = Department.objects.create(code="CSE", name="CSE")
    ece = Department.objects.create(code="ECE", name="ECE")
    return cse, ece


def test_cross_department_isolation_returns_404_not_403(stub_iam, two_depts):
    _cse, ece = two_depts
    ece_ann = Announcement.objects.create(
        department=ece, title="ECE Only", content="Body", target_roles=["all"],
        status="active", created_by_user_id=4002,
    )
    cse_hod = _as(stub_iam, uid=3001, role="HOD (CSE)", kind="faculty")
    assert cse_hod.get(f"/api/v1/department/departments/{ece.pk}").status_code == 404
    assert cse_hod.get(f"/api/v1/department/announcements/{ece_ann.pk}").status_code == 404
    assert cse_hod.delete(f"/api/v1/department/announcements/{ece_ann.pk}").status_code == 404

    # CSE Dept_Admin cannot create inventory in ECE by passing ECE's department_id.
    cse_admin = _as(stub_iam, uid=4001, role="deptadmin_cse", kind="staff")
    assert cse_admin.post(
        "/api/v1/department/inventory",
        {"department_id": ece.pk, "sku": "X", "name": "X", "quantity": 5},
        format="json",
    ).status_code == 404


def test_feedback_confidentiality_and_hod_initial_review_gate(stub_iam, two_depts):
    # BR-DEPT-017 / BR-DEPT-018: submitter isolation + HOD cannot see unreviewed 'new' feedback.
    cse, _ = two_depts
    fb_a = Feedback.objects.create(
        department=cse, submitter_user_id=1001, submitter_role="student",
        subject="Private A", body="Secret A", status="new",
    )
    Feedback.objects.create(
        department=cse, submitter_user_id=1002, submitter_role="student",
        subject="Private B", body="Secret B", status="new",
    )

    stu_a = _as(stub_iam, uid=1001, role="student", kind="student")
    rows = stu_a.get("/api/v1/department/feedback").json()["results"]
    assert [r["id"] for r in rows] == [fb_a.pk]

    hod = _as(stub_iam, uid=3001, role="HOD (CSE)", kind="faculty")
    assert hod.get("/api/v1/department/feedback").json()["results"] == []
    assert hod.post(
        f"/api/v1/department/feedback/{fb_a.pk}/dispose",
        {"status": "resolved"},
        format="json",
    ).status_code == 404


def test_faculty_stock_request_and_movement_isolation(stub_iam, two_depts):
    # BR-DEPT-012 / AFR-DEPT-016: Faculty sees only own requests and own issued stock history.
    cse, _ = two_depts
    item = InventoryItem.objects.create(
        department=cse, sku="CABLE-1", name="Cable", current_quantity=10, created_by_user_id=4001
    )
    req_a = StockRequest.objects.create(
        department=cse, item=item, requester_user_id=2001, requested_quantity=2, status="issued"
    )
    req_b = StockRequest.objects.create(
        department=cse, item=item, requester_user_id=2002, requested_quantity=3, status="issued"
    )
    StockMovement.objects.create(
        department=cse, item=item, stock_request=req_a, movement_type="issuance",
        quantity_delta=-2, balance_after=8, actor_user_id=4001,
    )
    StockMovement.objects.create(
        department=cse, item=item, stock_request=req_b, movement_type="issuance",
        quantity_delta=-3, balance_after=5, actor_user_id=4001,
    )
    StockMovement.objects.create(
        department=cse, item=item, stock_request=None, movement_type="insertion",
        quantity_delta=10, balance_after=10, actor_user_id=4001,
    )

    fac_a = _as(stub_iam, uid=2001, role="faculty", kind="faculty")
    reqs = fac_a.get("/api/v1/department/stock-requests").json()["results"]
    assert [r["id"] for r in reqs] == [req_a.pk]
    movs = fac_a.get("/api/v1/department/stock-movements").json()["results"]
    assert len(movs) == 1
    assert movs[0]["stock_request_id"] == req_a.pk


def test_profile_visibility_and_sensitive_pii_exclusion(stub_iam, two_depts):
    # BR-DEPT-019 / AFR-DEPT-025..028: sensitive_personal_data never exposed to any role.
    cse, _ = two_depts
    stu_enrolled = DepartmentProfile.objects.create(
        department=cse, user_id=1001, profile_kind="student", display_name="Enrolled Stu",
        email="e@inst.ac.in", program="BTech", academic_year="2026",
        academic_notes="Notes", sensitive_personal_data={"aadhaar": "1234"},
    )
    stu_other = DepartmentProfile.objects.create(
        department=cse, user_id=1002, profile_kind="student", display_name="Other Stu",
        program="BTech", sensitive_personal_data={"phone": "9999"},
    )
    alumni = DepartmentProfile.objects.create(
        department=cse, user_id=3005, profile_kind="alumni", display_name="Alum",
        graduation_year=2021, current_affiliation="Corp",
        sensitive_personal_data={"dob": "1999-01-01"},
    )
    CourseEnrollment.objects.create(
        department=cse, course_code="CS201", faculty_user_id=2001, student_user_id=1001
    )

    # Faculty 2001 sees enrolled student and alumni, gets 404 on unenrolled student.
    fac = _as(stub_iam, uid=2001, role="faculty", kind="faculty")
    assert fac.get(f"/api/v1/department/profiles/{stu_enrolled.pk}").status_code == 200
    assert fac.get(f"/api/v1/department/profiles/{stu_other.pk}").status_code == 404
    assert fac.get(f"/api/v1/department/profiles/{alumni.pk}").status_code == 200

    # Student gets 404 on alumni and never sees academic_notes on peer.
    stu = _as(stub_iam, uid=1002, role="student", kind="student")
    assert stu.get(f"/api/v1/department/profiles/{alumni.pk}").status_code == 404
    peer = stu.get(f"/api/v1/department/profiles/{stu_enrolled.pk}").json()
    assert "academic_notes" not in peer
    assert "sensitive_personal_data" not in peer

    # HOD sees all profiles, still never sees sensitive_personal_data.
    hod = _as(stub_iam, uid=3001, role="HOD (CSE)", kind="faculty")
    full = hod.get(f"/api/v1/department/profiles/{stu_enrolled.pk}").json()
    assert full["academic_notes"] == "Notes"
    assert "sensitive_personal_data" not in full
