from modules.department.models.announcements import Announcement
from modules.department.models.department import (
    Department,
    DepartmentProgram,
    OfficialDetailChange,
)
from modules.department.models.feedback import Feedback, FeedbackTransition
from modules.department.models.inventory import InventoryItem, StockMovement, StockRequest
from modules.department.models.notifications import DepartmentNotification
from modules.department.models.profiles import CourseEnrollment, DepartmentProfile
from modules.department.models.resources import LabResource, TimetableSlot
from modules.department.models.roles import DepartmentRoleAssignment

__all__ = [
    "Announcement",
    "CourseEnrollment",
    "Department",
    "DepartmentNotification",
    "DepartmentProfile",
    "DepartmentProgram",
    "DepartmentRoleAssignment",
    "Feedback",
    "FeedbackTransition",
    "InventoryItem",
    "LabResource",
    "OfficialDetailChange",
    "StockMovement",
    "StockRequest",
    "TimetableSlot",
]
