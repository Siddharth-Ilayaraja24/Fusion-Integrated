"""Department domain tables, split by aggregate."""
from modules.department.models.departments import Department
from modules.department.models.notifications import DepartmentNotification
from modules.department.models.role_assignments import DepartmentRoleAssignment

__all__ = [
    "Department",
    "DepartmentNotification",
    "DepartmentRoleAssignment",
]
