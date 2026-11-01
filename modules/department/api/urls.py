from django.urls import path

from modules.department.api import announcements_views as a
from modules.department.api import role_assignments_views as ra
from modules.department.api import views as v

urlpatterns = [
    path("departments", v.DepartmentListView.as_view(), name="department-departments"),
    path("assignments", ra.RoleAssignmentListView.as_view(), name="department-assignments"),
    path("announcements", a.AnnouncementListView.as_view(), name="department-announcements-list"),
    path("announcements/<int:pk>", a.AnnouncementDetailView.as_view(), name="department-announcement-detail"),
    path("announcements/<int:pk>/hide", a.AnnouncementHideView.as_view(), name="department-announcement-hide"),
]
