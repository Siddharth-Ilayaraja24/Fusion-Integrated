from datetime import time

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from conftest import make_session
from modules.department import registry
from modules.department.models import (
    Announcement,
    Department,
    DepartmentProgram,
    Feedback,
    InventoryItem,
    LabResource,
    StockMovement,
    StockRequest,
    TimetableSlot,
)

pytestmark = pytest.mark.django_db


def _admin_client(stub_iam):
    stub_iam(
        make_session(
            user_id=4001, kind="staff", roles=("dept_admin",), active_role="dept_admin",
            modules=("department",), permissions=tuple(registry.ROLE_GRANTS["dept_admin"]),
        )
    )
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION="Token tok")
    return c


def _seed_rows(dept: Department, start: int, count: int) -> None:
    for n in range(start, start + count):
        item = InventoryItem.objects.create(
            department=dept, sku=f"SKU-{n}", name=f"Item {n}", current_quantity=10,
            created_by_user_id=4001,
        )
        req = StockRequest.objects.create(
            department=dept, item=item, requester_user_id=2000 + n, requested_quantity=1,
            status="pending_hod_approval",
        )
        StockMovement.objects.create(
            department=dept, item=item, stock_request=req, movement_type="insertion",
            quantity_delta=10, balance_after=10, actor_user_id=4001,
        )
        Announcement.objects.create(
            department=dept, title=f"Ann {n}", content="Body", target_roles=["all"],
            status="active", created_by_user_id=4001,
        )
        Feedback.objects.create(
            department=dept, submitter_user_id=1000 + n, submitter_role="student",
            subject=f"Fb {n}", body="Body", status="new",
        )
        TimetableSlot.objects.create(
            department=dept, slot_kind="class", program="BTech", academic_year="2026-27",
            section=f"S{n}", course_code=f"CS{n}", course_title=f"Course {n}",
            room=f"R-{n}", day_of_week=n % 5, start_time=time(9, 0), end_time=time(10, 0),
            updated_by_user_id=4001,
        )
        LabResource.objects.create(
            department=dept, lab_code=f"LAB-{n}", name=f"Lab {n}", updated_by_user_id=4001,
        )
        DepartmentProgram.objects.create(
            department=dept, code=f"PROG-{n}", name=f"Prog {n}", degree_level="UG",
        )


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/department/inventory",
        "/api/v1/department/stock-requests",
        "/api/v1/department/stock-movements",
        "/api/v1/department/feedback",
        "/api/v1/department/timetables",
        "/api/v1/department/labs",
        "/api/v1/department/programs",
    ],
)
def test_list_endpoint_query_count_is_constant_in_row_count(stub_iam, path):
    dept = Department.objects.create(code="CSE", name="CSE")
    _seed_rows(dept, 0, 2)
    client = _admin_client(stub_iam)

    with CaptureQueriesContext(connection) as small:
        assert client.get(path).status_code == 200

    _seed_rows(dept, 2, 10)

    with CaptureQueriesContext(connection) as large:
        assert client.get(path).status_code == 200

    assert len(large) == len(small), (
        f"{path}: {len(small)} queries at 2 rows vs {len(large)} at 12 rows"
    )
