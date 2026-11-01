from django.urls import path

from modules.department.api import role_assignments_views as ra
from modules.department.api import views as v

urlpatterns = [
    path("departments", v.DepartmentListView.as_view(), name="department-departments"),
    path("assignments", ra.RoleAssignmentListView.as_view(), name="department-assignments"),
]
