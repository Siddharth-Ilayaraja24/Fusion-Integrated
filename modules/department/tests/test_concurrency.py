import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

import pytest
from django.db import IntegrityError, connection
from django.utils import timezone

from conftest import make_principal
from core.api.exceptions import ConflictError
from modules.department import registry
from modules.department.models import (
    Department,
    DepartmentRoleAssignment,
    InventoryItem,
    StockRequest,
)
from modules.department.services import inventory as inventory_svc


@pytest.mark.django_db(transaction=True)
def test_concurrent_stock_issuance_never_drives_inventory_negative():
    # AFR-DEPT-013 / BR-DEPT-016: real threads released on a barrier against real Postgres.
    cse = Department.objects.create(code="CSE", name="CSE")
    item = InventoryItem.objects.create(
        department=cse, sku="GPU-01", name="GPU", current_quantity=5, created_by_user_id=4001
    )
    r1 = StockRequest.objects.create(
        department=cse, item=item, requester_user_id=2001, requested_quantity=4,
        status="approved_for_issuance",
    )
    r2 = StockRequest.objects.create(
        department=cse, item=item, requester_user_id=2002, requested_quantity=4,
        status="approved_for_issuance",
    )
    admin = make_principal(
        user_id=4001, kind="staff", roles=("deptadmin_cse",), active_role="deptadmin_cse",
        modules=("department",), permissions=tuple(registry.ROLE_GRANTS["deptadmin_cse"]),
    )

    barrier = threading.Barrier(2)

    def _issue(req_id: int) -> str:
        try:
            barrier.wait(timeout=5)
            inventory_svc.issue_stock(request_id=req_id, actor=admin)
        except ConflictError:
            return "conflict"
        else:
            return "ok"
        finally:
            connection.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(_issue, [r1.pk, r2.pk]))

    assert outcomes.count("ok") == 1
    assert outcomes.count("conflict") == 1
    item.refresh_from_db()
    assert item.current_quantity == 1


@pytest.mark.django_db(transaction=True)
def test_partial_unique_constraint_prevents_two_active_hods():
    # BR-DEPT-022: DB-level backstop even if the service layer is bypassed.
    cse = Department.objects.create(code="CSE", name="CSE")
    now = timezone.now()
    DepartmentRoleAssignment.objects.create(
        department=cse, role_type="hod", user_id=3001,
        valid_from=now - timedelta(days=1), valid_to=now + timedelta(days=30),
        status="active", assigned_by_user_id=9001,
    )
    with pytest.raises(IntegrityError):
        DepartmentRoleAssignment.objects.create(
            department=cse, role_type="hod", user_id=3002,
            valid_from=now - timedelta(days=1), valid_to=now + timedelta(days=30),
            status="active", assigned_by_user_id=9001,
        )
