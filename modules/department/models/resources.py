from django.db import models
from django.db.models import F, Q

from core.db.mixins import TimeStampedModel
from modules.department.models.department import Department


class TimetableSlot(TimeStampedModel):
    KIND_CHOICES = [
        ("class", "Class"),
        ("lab", "Lab"),
    ]

    department = models.ForeignKey(
        Department, on_delete=models.CASCADE, related_name="timetable_slots"
    )
    slot_kind = models.CharField(max_length=16, choices=KIND_CHOICES, default="class")
    program = models.CharField(max_length=64)
    academic_year = models.CharField(max_length=32)
    section = models.CharField(max_length=32, default="A")
    course_code = models.CharField(max_length=32)
    course_title = models.CharField(max_length=160)
    faculty_user_id = models.IntegerField(null=True, blank=True)
    room = models.CharField(max_length=64)
    day_of_week = models.PositiveSmallIntegerField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)
    updated_by_user_id = models.IntegerField()

    class Meta:
        ordering = ["day_of_week", "start_time", "id"]
        constraints = [
            models.CheckConstraint(
                condition=Q(end_time__gt=F("start_time")),
                name="dept_tt_end_after_start",
            ),
            models.CheckConstraint(
                condition=Q(day_of_week__gte=0) & Q(day_of_week__lte=6),
                name="dept_tt_day_range",
            ),
        ]
        indexes = [
            models.Index(
                fields=["department", "day_of_week", "start_time"],
                name="dept_tt_dept_day_time_idx",
            ),
            models.Index(
                fields=["department", "program", "academic_year"],
                name="dept_tt_cohort_idx",
            ),
        ]


class LabResource(TimeStampedModel):
    STATUS_CHOICES = [
        ("operational", "Operational"),
        ("maintenance", "Under Maintenance"),
        ("decommissioned", "Decommissioned"),
    ]

    department = models.ForeignKey(
        Department, on_delete=models.CASCADE, related_name="lab_resources"
    )
    lab_code = models.CharField(max_length=32)
    name = models.CharField(max_length=160)
    location = models.CharField(max_length=160, blank=True)
    equipment_summary = models.TextField(blank=True)
    capacity = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=24, choices=STATUS_CHOICES, default="operational")
    incharge_user_id = models.IntegerField(null=True, blank=True)
    updated_by_user_id = models.IntegerField()

    class Meta:
        ordering = ["lab_code"]
        constraints = [
            models.UniqueConstraint(
                fields=["department", "lab_code"],
                name="dept_lab_unique_code",
            ),
        ]
        indexes = [
            models.Index(fields=["department", "status"], name="dept_lab_dept_status_idx"),
        ]
