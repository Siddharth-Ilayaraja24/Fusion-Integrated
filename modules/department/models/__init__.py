"""Department domain tables, split by aggregate."""
from modules.department.models.announcements import Announcement
from modules.department.models.departments import Department
from modules.department.models.feedback import Feedback
from modules.department.models.inventory import InventoryItem, StockMovement, StockRequest
from modules.department.models.notifications import DepartmentNotification
from modules.department.models.role_assignments import DepartmentRoleAssignment
from modules.department.models.timetable import AcademicProgram, LabResource, TimetableSlot

__all__ = [
    "AcademicProgram",
    "Announcement",
    "Department",
    "DepartmentNotification",
    "DepartmentRoleAssignment",
    "Feedback",
    "InventoryItem",
    "LabResource",
    "StockMovement",
    "StockRequest",
    "TimetableSlot",
]
