"""Department domain tables, split by aggregate."""
from modules.department.models.departments import Department
from modules.department.models.notifications import DepartmentNotification

__all__ = [
    "Department",
    "DepartmentNotification",
]
