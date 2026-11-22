from django.db import models
from django.db.models import Q

from core.db.mixins import TimeStampedModel


class Department(TimeStampedModel):
    code = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    contact_email = models.EmailField(blank=True)
    location = models.CharField(max_length=160, blank=True)
    website_url = models.URLField(blank=True)
    core_policies = models.TextField(blank=True)
    # AFR-DEPT-053: derived from active HOD role assignment, never directly edited.
    active_hod_user_id = models.IntegerField(null=True, blank=True)
    active_dept_admin_user_id = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ["code"]
        indexes = [
            models.Index(fields=["code"], name="dept_code_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.code} - {self.name}"


class OfficialDetailChange(TimeStampedModel):
    FIELD_CHOICES = [
        ("name", "Department Name"),
        ("core_policies", "Core Policies"),
    ]
    STATUS_CHOICES = [
        ("pending_hod_approval", "Pending HOD Approval"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    department = models.ForeignKey(
        Department, on_delete=models.CASCADE, related_name="official_changes"
    )
    field_name = models.CharField(max_length=32, choices=FIELD_CHOICES)
    previous_value = models.TextField(blank=True)
    proposed_value = models.TextField()
    status = models.CharField(
        max_length=32, choices=STATUS_CHOICES, default="pending_hod_approval"
    )
    proposed_by_user_id = models.IntegerField()
    decided_by_user_id = models.IntegerField(null=True, blank=True)
    decided_at = models.DateTimeField(null=True, blank=True)
    decision_note = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ["-id"]
        constraints = [
            models.CheckConstraint(
                condition=Q(field_name__in=["name", "core_policies"]),
                name="dept_official_change_field_valid",
            ),
            models.CheckConstraint(
                condition=Q(status__in=["pending_hod_approval", "approved", "rejected"]),
                name="dept_official_change_status_valid",
            ),
        ]
        indexes = [
            models.Index(
                fields=["department", "status", "-id"],
                name="dept_offchg_dept_status_idx",
            ),
        ]


class DepartmentProgram(TimeStampedModel):
    department = models.ForeignKey(
        Department, on_delete=models.CASCADE, related_name="programs"
    )
    code = models.CharField(max_length=32)
    name = models.CharField(max_length=160)
    degree_level = models.CharField(max_length=64)
    duration_years = models.PositiveSmallIntegerField(default=4)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["code"]
        constraints = [
            models.UniqueConstraint(
                fields=["department", "code"],
                name="dept_program_unique_code",
            ),
        ]
        indexes = [
            models.Index(fields=["department", "is_active"], name="dept_prog_dept_active_idx"),
        ]
