from django.urls import path

from modules.department.api.views import DepartmentListView

urlpatterns = [
    path("departments", DepartmentListView.as_view(), name="department-departments"),
]
