from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from conftest import make_session
from core.api import csrf
from modules.department import registry
from modules.department.models import (
    Announcement,
    Department,
    Feedback,
    InventoryItem,
    OfficialDetailChange,
    StockRequest,
)

pytestmark = pytest.mark.django_db


def _as(stub_iam, *, uid: int, perms=(), modules=("department",), role="student", kind="student"):
    stub_iam(
        make_session(
            user_id=uid, kind=kind, roles=(role,), active_role=role,
            modules=modules, permissions=perms,
        )
    )
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Token tok")
    return client


@pytest.fixture
def world():
    cse = Department.objects.create(code="CSE", name="CSE")
    item = InventoryItem.objects.create(
        department=cse, sku="M-1", name="Marker", current_quantity=10, created_by_user_id=4001
    )
    ann = Announcement.objects.create(
        department=cse, title="Notice", content="Body", target_roles=["all"],
        status="active", created_by_user_id=4001,
    )
    req = StockRequest.objects.create(
        department=cse, item=item, requester_user_id=2001, requested_quantity=2,
        status="pending_hod_approval",
    )
    fb = Feedback.objects.create(
        department=cse, submitter_user_id=1001, submitter_role="student",
        subject="Noise", body="Too loud", status="new",
    )
    chg = OfficialDetailChange.objects.create(
        department=cse, field_name="name", previous_value="CSE", proposed_value="CSE New",
        status="pending_hod_approval", proposed_by_user_id=4001,
    )
    return cse, item, ann, req, fb, chg


def test_every_role_grant_and_nav_permission_exists_in_registry_permissions():
    declared = {code for code, _ in registry.PERMISSIONS}
    for role, codes in registry.ROLE_GRANTS.items():
        assert set(codes) <= declared, f"Unknown permission in ROLE_GRANTS[{role!r}]"
    for item in registry.NAV_ITEMS:
        assert item["required_permission"] in declared


def test_both_gates_enforced_separately_and_unauthenticated_is_401(stub_iam, world):
    # No session -> 401.
    anon = APIClient()
    assert anon.get("/api/v1/department/departments").status_code == 401

    # Module grant without permission -> 403.
    no_perm = _as(stub_iam, uid=1001, perms=(), modules=("department",))
    assert no_perm.get("/api/v1/department/departments").status_code == 403

    # Permission without module grant -> 403.
    no_mod = _as(
        stub_iam, uid=1001, perms=("department.department.view",), modules=()
    )
    assert no_mod.get("/api/v1/department/departments").status_code == 403


def test_student_cannot_perform_privileged_writes(stub_iam, world):
    cse, item, ann, req, fb, chg = world
    stu = _as(
        stub_iam, uid=1001, perms=tuple(registry.ROLE_GRANTS["student"]),
        role="student", kind="student",
    )

    assert stu.post(
        "/api/v1/department/announcements",
        {"department_id": cse.pk, "title": "x", "content": "y", "target_roles": ["all"]},
        format="json",
    ).status_code == 403
    assert stu.patch(
        f"/api/v1/department/announcements/{ann.pk}", {"title": "hacked"}, format="json"
    ).status_code == 403
    assert stu.delete(f"/api/v1/department/announcements/{ann.pk}").status_code == 403
    assert stu.post(
        "/api/v1/department/inventory",
        {"department_id": cse.pk, "sku": "X", "name": "X", "quantity": 1},
        format="json",
    ).status_code == 403
    assert stu.post(
        "/api/v1/department/stock-requests",
        {"item_id": item.pk, "requested_quantity": 1},
        format="json",
    ).status_code == 403
    assert stu.post(
        f"/api/v1/department/stock-requests/{req.pk}/decide", {"approve": True}, format="json"
    ).status_code == 403
    assert stu.post(
        f"/api/v1/department/stock-requests/{req.pk}/issue", {}, format="json"
    ).status_code == 403
    assert stu.post(
        f"/api/v1/department/feedback/{fb.pk}/review", {"category": "x"}, format="json"
    ).status_code == 403
    assert stu.post(
        f"/api/v1/department/feedback/{fb.pk}/dispose", {"status": "closed"}, format="json"
    ).status_code == 403
    assert stu.post(
        f"/api/v1/department/official-changes/{chg.pk}/decide", {"approve": True}, format="json"
    ).status_code == 403
    assert stu.post(
        "/api/v1/department/role-assignments",
        {
            "department_id": cse.pk, "role_type": "hod", "user_id": 1001,
            "valid_from": timezone.now().isoformat(),
            "valid_to": (timezone.now() + timedelta(days=1)).isoformat(),
        },
        format="json",
    ).status_code == 403


def test_role_switch_restricts_to_acting_role_only(stub_iam, world):
    _, _, ann, _, _, _ = world
    # User holds both HOD (CSE) and faculty, but active_role is faculty with faculty grants.
    stub_iam(
        make_session(
            user_id=3001,
            kind="faculty",
            roles=("faculty", "HOD (CSE)"),
            active_role="faculty",
            modules=("department",),
            permissions=tuple(registry.ROLE_GRANTS["faculty"]),
        )
    )
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Token tok")
    assert client.delete(f"/api/v1/department/announcements/{ann.pk}").status_code == 403


def test_self_approval_and_headship_edit_blocked(stub_iam, world):
    cse, item, _, _, _, _ = world
    # HOD cannot approve their own stock request.
    own_req = StockRequest.objects.create(
        department=cse, item=item, requester_user_id=3001, requested_quantity=1,
        status="pending_hod_approval",
    )
    hod = _as(
        stub_iam, uid=3001, perms=tuple(registry.ROLE_GRANTS["HOD (CSE)"]),
        role="HOD (CSE)", kind="faculty",
    )
    assert hod.post(
        f"/api/v1/department/stock-requests/{own_req.pk}/decide", {"approve": True}, format="json"
    ).status_code == 409

    # HOD cannot approve an official change they proposed.
    own_chg = OfficialDetailChange.objects.create(
        department=cse, field_name="core_policies", previous_value="", proposed_value="x",
        status="pending_hod_approval", proposed_by_user_id=3001,
    )
    assert hod.post(
        f"/api/v1/department/official-changes/{own_chg.pk}/decide",
        {"approve": True},
        format="json",
    ).status_code == 409

    # Headship cannot be edited via official department change (AFR-DEPT-053).
    admin = _as(
        stub_iam, uid=4001, perms=tuple(registry.ROLE_GRANTS["deptadmin_cse"]),
        role="deptadmin_cse", kind="staff",
    )
    assert admin.post(
        "/api/v1/department/official-changes",
        {"department_id": cse.pk, "field_name": "headship", "proposed_value": "Someone"},
        format="json",
    ).status_code == 400

    # Dept_Admin cannot review their own feedback.
    own_fb = Feedback.objects.create(
        department=cse, submitter_user_id=4001, submitter_role="faculty",
        subject="Self", body="Body", status="new",
    )
    assert admin.post(
        f"/api/v1/department/feedback/{own_fb.pk}/review", {"category": "General"}, format="json"
    ).status_code == 409


def test_bad_query_parameter_returns_400_not_500(stub_iam, world):
    stu = _as(
        stub_iam, uid=1001, perms=tuple(registry.ROLE_GRANTS["student"]),
        role="student", kind="student",
    )
    assert stu.get("/api/v1/department/announcements?department=not-an-int").status_code == 400
    assert stu.get("/api/v1/department/timetables?day_of_week=monday").status_code == 400


def test_cookie_write_without_csrf_token_returns_403(stub_iam, world):
    cse, _, _, _, _, _ = world
    stub_iam(
        make_session(
            user_id=1001, kind="student", roles=("student",), active_role="student",
            modules=("department",), permissions=tuple(registry.ROLE_GRANTS["student"]),
        )
    )
    client = APIClient()
    client.cookies["fusion_session"] = "sess-123"
    no_csrf = client.post(
        "/api/v1/department/feedback",
        {"department_id": cse.pk, "subject": "S", "body": "B"},
        format="json",
    )
    assert no_csrf.status_code == 403

    with_csrf = client.post(
        "/api/v1/department/feedback",
        {"department_id": cse.pk, "subject": "S", "body": "B"},
        format="json",
        HTTP_X_CSRF_TOKEN=csrf.token_for("sess-123"),
    )
    assert with_csrf.status_code == 201
