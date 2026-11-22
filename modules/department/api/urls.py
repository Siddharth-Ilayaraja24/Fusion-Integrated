from django.urls import path

from modules.department.api import views

urlpatterns = [
    path("departments", views.DepartmentListView.as_view(), name="dept-list"),
    path("departments/<int:pk>", views.DepartmentDetailView.as_view(), name="dept-detail"),
    path("official-changes", views.OfficialChangeListCreateView.as_view(), name="dept-changes"),
    path(
        "official-changes/<int:pk>/decide",
        views.OfficialChangeDecideView.as_view(),
        name="dept-change-decide",
    ),
    path("announcements", views.AnnouncementListCreateView.as_view(), name="dept-announcements"),
    path(
        "announcements/<int:pk>",
        views.AnnouncementDetailView.as_view(),
        name="dept-announcement-detail",
    ),
    path(
        "announcements/<int:pk>/hide",
        views.AnnouncementHideView.as_view(),
        name="dept-announcement-hide",
    ),
    path("inventory", views.InventoryListCreateView.as_view(), name="dept-inventory"),
    path("stock-requests", views.StockRequestListCreateView.as_view(), name="dept-stock-requests"),
    path(
        "stock-requests/<int:pk>/decide",
        views.StockRequestDecideView.as_view(),
        name="dept-stock-decide",
    ),
    path(
        "stock-requests/<int:pk>/issue",
        views.StockRequestIssueView.as_view(),
        name="dept-stock-issue",
    ),
    path("stock-movements", views.StockMovementListView.as_view(), name="dept-stock-movements"),
    path("feedback", views.FeedbackListCreateView.as_view(), name="dept-feedback"),
    path("feedback/<int:pk>/review", views.FeedbackReviewView.as_view(), name="dept-fb-review"),
    path("feedback/<int:pk>/dispose", views.FeedbackDisposeView.as_view(), name="dept-fb-dispose"),
    path("timetables", views.TimetableListCreateView.as_view(), name="dept-timetables"),
    path("timetables/<int:pk>", views.TimetableDetailView.as_view(), name="dept-timetable-detail"),
    path("labs", views.LabResourceListCreateView.as_view(), name="dept-labs"),
    path("labs/<int:pk>", views.LabResourceDetailView.as_view(), name="dept-lab-detail"),
    path("programs", views.ProgramListCreateView.as_view(), name="dept-programs"),
    path("programs/<int:pk>", views.ProgramDetailView.as_view(), name="dept-program-detail"),
    path("profiles", views.ProfileListCreateView.as_view(), name="dept-profiles"),
    path("profiles/<int:pk>", views.ProfileDetailView.as_view(), name="dept-profile-detail"),
    path("roster", views.RosterListCreateView.as_view(), name="dept-roster"),
    path(
        "role-assignments",
        views.RoleAssignmentListCreateView.as_view(),
        name="dept-role-assignments",
    ),
]
