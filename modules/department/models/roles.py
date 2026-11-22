from django.db import models
from django.db.models import F, Q

from core.db.mixins import TimeStampedModel, UserScopedModel
from modules.department.models.department import Department


class DepartmentRoleAssignment(TimeStampedModel, UserScopedModel):
    ROLE_CHOICES = [
        ("hod", "HOD"),
        ("dept_admin", "Dept_Admin"),
    ]
    STATUS_CHOICES = [
        ("scheduled", "Scheduled"),
        ("active", "Active"),
        ("superseded", "Superseded"),
        ("expired", "Expired"),
        ("cancelled", "Cancelled"),
    ]

    department = models.ForeignKey(
        Department, on_delete=models.CASCADE, related_name="role_assignments"
    )
    role_type = models.CharField(max_length=16, choices=ROLE_CHOICES)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="scheduled")
    assigned_by_user_id = models.IntegerField()
    activated_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-valid_from", "-id"]
        constraints = [
            models.CheckConstraint(
                condition=Q(role_type__in=["hod", "dept_admin"]),
                name="dept_role_assign_type_valid",
            ),
            models.CheckConstraint(
                condition=Q(
                    status__in=["scheduled", "active", "superseded", "expired", "cancelled"]
                ),
                name="dept_role_assign_status_valid",
            ),
            # BR-DEPT-023: time-bounded tenure interval.
            models.CheckConstraint(
                condition=Q(valid_to__gt=F("valid_from")),
                name="dept_role_assign_tenure_valid",
            ),
            # BR-DEPT-022: at most one active HOD and one active Dept_Admin per department.
            models.UniqueConstraint(
                fields=["department", "role_type"],
                condition=Q(status="active"),
                name="dept_one_active_role_per_type",
            ),
        ]
        indexes = [
            models.Index(
                fields=["department", "role_type", "status"],
                name="dept_role_dept_type_st_idx",
            ),
            models.Index(
                fields=["status", "valid_from"],
                name="dept_role_status_from_idx",
            ),
        ]
