from django.db import models
from django.db.models import Q

from core.db.mixins import TimeStampedModel
from modules.department.models.department import Department


class DepartmentNotification(TimeStampedModel):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("sent", "Sent"),
        ("failed", "Failed"),
    ]

    department = models.ForeignKey(
        Department, on_delete=models.CASCADE, related_name="notifications"
    )
    topic = models.CharField(max_length=64)
    dedupe_key = models.CharField(max_length=160, unique=True)
    recipient_user_id = models.IntegerField()
    subject = models.CharField(max_length=200)
    body = models.TextField()
    payload = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="pending")
    attempts = models.PositiveSmallIntegerField(default=0)
    sent_at = models.DateTimeField(null=True, blank=True)
    last_error = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ["-id"]
        constraints = [
            models.CheckConstraint(
                condition=Q(status__in=["pending", "sent", "failed"]),
                name="dept_notif_status_valid",
            ),
        ]
        indexes = [
            models.Index(fields=["status", "id"], name="dept_notif_status_idx"),
            models.Index(fields=["recipient_user_id", "-id"], name="dept_notif_recip_idx"),
        ]
