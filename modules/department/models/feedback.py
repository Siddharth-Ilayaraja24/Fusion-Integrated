from django.db import models
from django.db.models import Q

from core.db.mixins import TimeStampedModel
from modules.department.models.department import Department


class Feedback(TimeStampedModel):
    STATUS_CHOICES = [
        ("new", "New"),
        ("under_review", "Under Review / Categorized"),
        ("resolved", "Resolved"),
        ("closed", "Closed"),
    ]

    department = models.ForeignKey(
        Department, on_delete=models.CASCADE, related_name="feedback_items"
    )
    submitter_user_id = models.IntegerField()
    submitter_role = models.CharField(max_length=32)
    subject = models.CharField(max_length=200)
    body = models.TextField()
    category = models.CharField(max_length=80, blank=True)
    status = models.CharField(max_length=24, choices=STATUS_CHOICES, default="new")
    initial_reviewed_by_user_id = models.IntegerField(null=True, blank=True)
    initial_reviewed_at = models.DateTimeField(null=True, blank=True)
    resolved_by_user_id = models.IntegerField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_note = models.TextField(blank=True)

    class Meta:
        ordering = ["-id"]
        constraints = [
            models.CheckConstraint(
                condition=Q(status__in=["new", "under_review", "resolved", "closed"]),
                name="dept_feedback_status_valid",
            ),
        ]
        indexes = [
            models.Index(
                fields=["department", "status", "-id"],
                name="dept_fb_dept_status_idx",
            ),
            models.Index(
                fields=["submitter_user_id", "-id"],
                name="dept_fb_submitter_idx",
            ),
        ]


class FeedbackTransition(models.Model):
    feedback = models.ForeignKey(
        Feedback, on_delete=models.CASCADE, related_name="transitions"
    )
    from_status = models.CharField(max_length=24)
    to_status = models.CharField(max_length=24)
    actor_user_id = models.IntegerField()
    actor_role = models.CharField(max_length=32)
    note = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]
        indexes = [
            models.Index(fields=["feedback", "id"], name="dept_fb_trans_fb_idx"),
        ]

    def __str__(self) -> str:
        return f"FeedbackTransition({self.feedback_id}: {self.from_status}->{self.to_status})"
