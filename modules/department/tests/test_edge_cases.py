from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from conftest import make_session
from modules.department import registry
from modules.department.models import (
    Department,
    DepartmentNotification,
    DepartmentRoleAssignment,
    Feedback,
    InventoryItem,
    StockRequest,
)
from modules.department.services import notifications, roles

pytestmark = pytest.mark.django_db


def _as(stub_iam, *, uid: int, role: str, kind: str = "staff"):
    stub_iam(
        make_session(
            user_id=uid, kind=kind, roles=(role,), active_role=role,
            modules=("department",), permissions=tuple(registry.ROLE_GRANTS[role]),
        )
    )
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION="Token tok")
    return c


def test_inventory_topup_and_duplicate_conflicts(stub_iam):
    cse = Department.objects.create(code="CSE", name="CSE")
    admin = _as(stub_iam, uid=4001, role="deptadmin_cse")

    # Insert new SKU, then top up the same SKU.
    r1 = admin.post(
        "/api/v1/department/inventory",
        {"department_id": cse.pk, "sku": "CBL-1", "name": "Cable", "quantity": 5,
         "category": "AV", "location": "Store", "description": "2m"},
        format="json",
    )
    assert r1.status_code == 201
    r2 = admin.post(
        "/api/v1/department/inventory",
        {"department_id": cse.pk, "sku": "cbl-1", "name": "HDMI Cable", "quantity": 7,
         "category": "AV2", "location": "Rack 2", "description": "3m"},
        format="json",
    )
    assert r2.status_code == 201
    assert r2.json()["current_quantity"] == 12

    # Duplicate lab code and program code return 409.
    assert admin.post(
        "/api/v1/department/labs",
        {"department_id": cse.pk, "lab_code": "L1", "name": "Lab 1"},
        format="json",
    ).status_code == 201
    assert admin.post(
        "/api/v1/department/labs",
        {"department_id": cse.pk, "lab_code": "L1", "name": "Dup"},
        format="json",
    ).status_code == 409

    assert admin.post(
        "/api/v1/department/programs",
        {"department_id": cse.pk, "code": "BT", "name": "BTech"},
        format="json",
    ).status_code == 201
    assert admin.post(
        "/api/v1/department/programs",
        {"department_id": cse.pk, "code": "BT", "name": "Dup"},
        format="json",
    ).status_code == 409


def test_profile_update_duplicate_and_roster_listing(stub_iam):
    cse = Department.objects.create(code="CSE", name="CSE")
    admin = _as(stub_iam, uid=4001, role="deptadmin_cse")
    p = admin.post(
        "/api/v1/department/profiles",
        {"department_id": cse.pk, "user_id": 1001, "profile_kind": "student",
         "display_name": "Asha"},
        format="json",
    )
    assert p.status_code == 201
    pid = p.json()["id"]
    # Duplicate profile for same (department, user_id) -> 409.
    assert admin.post(
        "/api/v1/department/profiles",
        {"department_id": cse.pk, "user_id": 1001, "profile_kind": "student",
         "display_name": "Asha"},
        format="json",
    ).status_code == 409

    # PATCH profile + list with filters + roster list.
    assert admin.patch(
        f"/api/v1/department/profiles/{pid}",
        {"display_name": "Asha V.", "email": "asha@inst.ac.in"},
        format="json",
    ).status_code == 200
    assert len(
        admin.get(f"/api/v1/department/profiles?department={cse.pk}&profile_kind=student")
        .json()["results"]
    ) == 1
    assert admin.post(
        "/api/v1/department/roster",
        {"department_id": cse.pk, "course_code": "CS101",
         "faculty_user_id": 2001, "student_user_id": 2001},
        format="json",
    ).status_code == 400
    assert admin.post(
        "/api/v1/department/roster",
        {"department_id": cse.pk, "course_code": "CS101",
         "faculty_user_id": 2001, "student_user_id": 1001},
        format="json",
    ).status_code == 201
    assert len(admin.get(f"/api/v1/department/roster?department={cse.pk}").json()["results"]) == 1


def test_state_conflict_and_404_error_paths(stub_iam):
    cse = Department.objects.create(code="CSE", name="CSE")
    item = InventoryItem.objects.create(
        department=cse, sku="X1", name="X", current_quantity=5, created_by_user_id=4001
    )
    req = StockRequest.objects.create(
        department=cse, item=item, requester_user_id=2001, requested_quantity=2,
        status="pending_hod_approval",
    )
    fb = Feedback.objects.create(
        department=cse, submitter_user_id=1001, submitter_role="student",
        subject="S", body="B", status="new",
    )

    admin = _as(stub_iam, uid=4001, role="deptadmin_cse")
    # Issuing unapproved stock request -> 409.
    assert admin.post(f"/api/v1/department/stock-requests/{req.pk}/issue", {},
                      format="json").status_code == 409
    # Disposing unreviewed feedback -> 409.
    assert admin.post(f"/api/v1/department/feedback/{fb.pk}/dispose", {"status": "closed"},
                      format="json").status_code == 409
    # Review then re-review -> 409.
    assert admin.post(f"/api/v1/department/feedback/{fb.pk}/review", {"category": "Lab"},
                      format="json").status_code == 200
    assert admin.post(f"/api/v1/department/feedback/{fb.pk}/review", {"category": "Lab"},
                      format="json").status_code == 409
    # 404 on unknown IDs.
    assert admin.get("/api/v1/department/departments/999999").status_code == 404
    assert admin.get("/api/v1/department/announcements/999999").status_code == 404
    assert admin.patch("/api/v1/department/timetables/999999", {"room": "R1"},
                       format="json").status_code == 404
    assert admin.patch("/api/v1/department/labs/999999", {"name": "L"},
                       format="json").status_code == 404
    assert admin.patch("/api/v1/department/programs/999999", {"name": "P"},
                       format="json").status_code == 404
    assert admin.patch("/api/v1/department/profiles/999999", {"display_name": "P"},
                       format="json").status_code == 404
    assert admin.post("/api/v1/department/stock-requests/999999/issue", {},
                      format="json").status_code == 404
    assert admin.post("/api/v1/department/feedback/999999/review", {"category": "X"},
                      format="json").status_code == 404
    assert admin.post("/api/v1/department/feedback/999999/dispose", {"status": "closed"},
                      format="json").status_code == 404
    assert admin.get(f"/api/v1/department/official-changes?department={cse.pk}").status_code == 200
    assert admin.get(f"/api/v1/department/stock-requests?department={cse.pk}&status=pending_hod_approval").status_code == 200
    assert admin.get(f"/api/v1/department/timetables?department={cse.pk}&day_of_week=1&program=BTech").status_code == 200
    assert admin.get(f"/api/v1/department/labs?department={cse.pk}").status_code == 200
    assert admin.get(f"/api/v1/department/programs?department={cse.pk}").status_code == 200
    assert admin.get(f"/api/v1/department/stock-movements?department={cse.pk}").status_code == 200
    assert admin.get(f"/api/v1/department/feedback?department={cse.pk}").status_code == 200
    assert admin.get(f"/api/v1/department/inventory?department={cse.pk}").status_code == 200
    assert admin.get(f"/api/v1/department/announcements?department={cse.pk}").status_code == 200

    # HOD 404s and double-decision conflicts.
    hod = _as(stub_iam, uid=3001, role="HOD (CSE)", kind="faculty")
    assert hod.post("/api/v1/department/stock-requests/999999/decide", {"approve": True},
                    format="json").status_code == 404
    assert hod.post("/api/v1/department/official-changes/999999/decide", {"approve": True},
                    format="json").status_code == 404
    assert hod.post(f"/api/v1/department/stock-requests/{req.pk}/decide", {"approve": False},
                    format="json").status_code == 200
    assert hod.post(f"/api/v1/department/stock-requests/{req.pk}/decide", {"approve": True},
                    format="json").status_code == 409


def test_role_assignment_edge_cases_and_expiry(stub_iam):
    cse = Department.objects.create(code="CSE", name="CSE")
    inst = _as(stub_iam, uid=9001, role="acadadmin")
    now = timezone.now()

    # Inverted tenure -> 400.
    assert inst.post(
        "/api/v1/department/role-assignments",
        {"department_id": cse.pk, "role_type": "hod", "user_id": 3001,
         "valid_from": (now + timedelta(days=5)).isoformat(),
         "valid_to": (now + timedelta(days=1)).isoformat()},
        format="json",
    ).status_code == 400
    # Past valid_to -> 400.
    assert inst.post(
        "/api/v1/department/role-assignments",
        {"department_id": cse.pk, "role_type": "hod", "user_id": 3001,
         "valid_from": (now - timedelta(days=5)).isoformat(),
         "valid_to": (now - timedelta(days=1)).isoformat()},
        format="json",
    ).status_code == 400
    # Missing department -> 404.
    assert inst.post(
        "/api/v1/department/role-assignments",
        {"department_id": 999999, "role_type": "hod", "user_id": 3001,
         "valid_from": now.isoformat(), "valid_to": (now + timedelta(days=5)).isoformat()},
        format="json",
    ).status_code == 404

    # Overlapping scheduled assignment -> 409.
    assert inst.post(
        "/api/v1/department/role-assignments",
        {"department_id": cse.pk, "role_type": "hod", "user_id": 3001,
         "valid_from": (now + timedelta(days=10)).isoformat(),
         "valid_to": (now + timedelta(days=20)).isoformat()},
        format="json",
    ).status_code == 201
    assert inst.post(
        "/api/v1/department/role-assignments",
        {"department_id": cse.pk, "role_type": "hod", "user_id": 3002,
         "valid_from": (now + timedelta(days=15)).isoformat(),
         "valid_to": (now + timedelta(days=25)).isoformat()},
        format="json",
    ).status_code == 409
    assert len(inst.get(f"/api/v1/department/role-assignments?department={cse.pk}").json()["results"]) == 1

    # Active assignment expires when valid_to passes.
    DepartmentRoleAssignment.objects.create(
        department=cse, role_type="dept_admin", user_id=4001,
        valid_from=now - timedelta(days=10), valid_to=now - timedelta(minutes=1),
        status="active", assigned_by_user_id=9001,
    )
    cse.active_dept_admin_user_id = 4001
    cse.save(update_fields=["active_dept_admin_user_id"])
    assert roles.apply_effective_transitions(now=now) == 1
    cse.refresh_from_db()
    assert cse.active_dept_admin_user_id is None


def test_notification_delivery_failure_marks_failed_after_max_attempts(stub_iam, user_ref, settings):
    settings.NOTIFY_MAX_ATTEMPTS = 1
    stub_iam(users={1001: user_ref(1001)})
    cse = Department.objects.create(code="CSE", name="CSE")
    note = DepartmentNotification.objects.create(
        department=cse, topic="feedback.resolved", dedupe_key="fail-1",
        recipient_user_id=1001, subject="Subj", body="Body",
    )
    from fusion_auth.client import UserRef

    with patch("modules.department.services.notifications.send_mail", side_effect=OSError("smtp")):
        stub_iam(
            users={
                1001: UserRef(
                    user_id=1001,
                    username="u1001",
                    display_name="Asha",
                    kind="student",
                    email="a@inst.ac.in",
                )
            }
        )
        assert notifications.deliver_pending() == 0
    note.refresh_from_db()
    assert note.status == "failed"
    assert note.attempts == 1


def test_feedback_throttling_returns_429(stub_iam, settings):
    cse = Department.objects.create(code="CSE", name="CSE")
    stu = _as(stub_iam, uid=1050, role="student", kind="student")
    orig = settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["dept_feedback"]
    settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["dept_feedback"] = "1/min"
    try:
        assert stu.post(
            "/api/v1/department/feedback",
            {"department_id": cse.pk, "subject": "S1", "body": "B1"},
            format="json",
        ).status_code == 201
        assert stu.post(
            "/api/v1/department/feedback",
            {"department_id": cse.pk, "subject": "S2", "body": "B2"},
            format="json",
        ).status_code == 429
    finally:
        settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["dept_feedback"] = orig
