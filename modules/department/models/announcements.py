from django.db import models
from django.db.models import Q

from core.db.mixins import TimeStampedModel
from modules.department.models.department import Department


class Announcement(TimeStampedModel):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("hidden", "Hidden"),
        ("deleted", "Deleted"),
    ]

    department = models.ForeignKey(
        Department, on_delete=models.CASCADE, related_name="announcements"
    )
    title = models.CharField(max_length=200)
    content = models.TextField()
    target_roles = models.JSONField(default=list)
    target_programs = models.JSONField(default=list)
    target_academic_years = models.JSONField(default=list)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="active")
    created_by_user_id = models.IntegerField()
    updated_by_user_id = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ["-id"]
        constraints = [
            models.CheckConstraint(
                condition=Q(status__in=["active", "hidden", "deleted"]),
                name="dept_announcement_status_valid",
            ),
        ]
        indexes = [
            models.Index(
                fields=["department", "status", "-id"],
                name="dept_ann_dept_status_idx",
            ),
        ]
