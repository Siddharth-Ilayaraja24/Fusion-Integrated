from datetime import timedelta

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.utils import timezone

from config.celery import app
from modules.department import contracts, registry, tasks
from modules.department.models import (
    Department,
    DepartmentNotification,
    DepartmentRoleAssignment,
    InventoryItem,
)
from modules.department.schedule import BEAT_SCHEDULE, TASK_ROUTES


def test_every_department_beat_entry_is_registered_and_merged():
    for key, entry in BEAT_SCHEDULE.items():
        assert key in app.conf.beat_schedule
        assert entry["task"] in app.tasks
        assert entry["options"]["expires"] > 0


def test_every_department_task_routed_to_served_queue():
    served = {"default", "notifications", "reports", "ingest"}
    for task_name, route in TASK_ROUTES.items():
        assert route["queue"] in served, f"{task_name} routed to unknown queue {route['queue']}"


@pytest.mark.django_db
def test_scheduled_tasks_are_idempotent(stub_iam, user_ref):
    stub_iam(users={1001: user_ref(1001)})
    cse = Department.objects.create(code="CSE", name="CSE")
    now = timezone.now()
    DepartmentRoleAssignment.objects.create(
        department=cse, role_type="hod", user_id=3001,
        valid_from=now - timedelta(minutes=5), valid_to=now + timedelta(days=30),
        status="scheduled", assigned_by_user_id=9001,
    )
    DepartmentNotification.objects.create(
        department=cse, topic="announcement.published", dedupe_key="k1",
        recipient_user_id=1001, subject="Subj", body="Body",
    )

    assert tasks.apply_role_transitions() == 1
    assert tasks.apply_role_transitions() == 0
    assert tasks.deliver_notifications() == 1
    assert tasks.deliver_notifications() == 0


@pytest.mark.django_db
def test_management_commands_readiness_and_contracts():
    assert len(registry.readiness()) == 1
    with pytest.raises(CommandError):
        call_command("check_department_readiness")

    call_command("seed_departments")
    assert registry.readiness() == []
    call_command("check_department_readiness")
    call_command("run_department_tasks")

    cse = Department.objects.get(code="CSE")
    item = InventoryItem.objects.create(
        department=cse, sku="P-1", name="Projector", current_quantity=3, created_by_user_id=4001
    )
    assert contracts.get_departments([cse.pk])[cse.pk].code == "CSE"
    assert contracts.get_departments([]) == {}
    assert contracts.get_active_role_holders([cse.pk])[cse.pk].code == "CSE"
    assert contracts.get_active_role_holders([]) == {}
    assert contracts.get_inventory_items([item.pk])[item.pk].sku == "P-1"
    assert contracts.get_inventory_items([]) == {}
