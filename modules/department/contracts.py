from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from modules.department.models import Department, InventoryItem


@dataclass(frozen=True)
class DepartmentDTO:
    id: int
    code: str
    name: str
    active_hod_user_id: int | None
    active_dept_admin_user_id: int | None


@dataclass(frozen=True)
class DepartmentLeadershipDTO:
    department_id: int
    code: str
    active_hod_user_id: int | None
    active_dept_admin_user_id: int | None


@dataclass(frozen=True)
class InventoryItemDTO:
    id: int
    department_id: int
    sku: str
    name: str
    current_quantity: int


def get_departments(department_ids: Sequence[int]) -> dict[int, DepartmentDTO]:
    ids = {int(i) for i in department_ids if i is not None}
    if not ids:
        return {}
    return {
        d.pk: DepartmentDTO(
            id=d.pk,
            code=d.code,
            name=d.name,
            active_hod_user_id=d.active_hod_user_id,
            active_dept_admin_user_id=d.active_dept_admin_user_id,
        )
        for d in Department.objects.filter(pk__in=ids)
    }


def get_active_role_holders(department_ids: Sequence[int]) -> dict[int, DepartmentLeadershipDTO]:
    ids = {int(i) for i in department_ids if i is not None}
    if not ids:
        return {}
    return {
        d.pk: DepartmentLeadershipDTO(
            department_id=d.pk,
            code=d.code,
            active_hod_user_id=d.active_hod_user_id,
            active_dept_admin_user_id=d.active_dept_admin_user_id,
        )
        for d in Department.objects.filter(pk__in=ids)
    }


def get_inventory_items(item_ids: Sequence[int]) -> dict[int, InventoryItemDTO]:
    ids = {int(i) for i in item_ids if i is not None}
    if not ids:
        return {}
    return {
        i.pk: InventoryItemDTO(
            id=i.pk,
            department_id=i.department_id,
            sku=i.sku,
            name=i.name,
            current_quantity=i.current_quantity,
        )
        for i in InventoryItem.objects.filter(pk__in=ids)
    }
