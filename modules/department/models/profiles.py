from django.db import models
from django.db.models import Q

from core.db.mixins import TimeStampedModel, UserScopedModel
from modules.department.models.department import Department


class DepartmentProfile(TimeStampedModel, UserScopedModel):
    KIND_CHOICES = [
        ("student", "Student"),
        ("faculty", "Faculty"),
        ("alumni", "Alumni"),
    ]

    department = models.ForeignKey(
        Department, on_delete=models.CASCADE, related_name="profiles"
    )
    profile_kind = models.CharField(max_length=16, choices=KIND_CHOICES)
    display_name = models.CharField(max_length=160)
    email = models.EmailField(blank=True)
    program = models.CharField(max_length=64, blank=True)
    academic_year = models.CharField(max_length=32, blank=True)
    designation_title = models.CharField(max_length=120, blank=True)
    office_room = models.CharField(max_length=64, blank=True)
    research_area = models.CharField(max_length=200, blank=True)
    graduation_year = models.PositiveSmallIntegerField(null=True, blank=True)
    current_affiliation = models.CharField(max_length=160, blank=True)
    academic_notes = models.TextField(blank=True)
    # BR-DEPT-019 / AFR-DEPT-028: structurally isolated, never exposed in API responses.
    sensitive_personal_data = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["display_name", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["department", "user_id"],
                name="dept_profile_unique_user",
            ),
            models.CheckConstraint(
                condition=Q(profile_kind__in=["student", "faculty", "alumni"]),
                name="dept_profile_kind_valid",
            ),
        ]
        indexes = [
            models.Index(
                fields=["department", "profile_kind"],
                name="dept_prof_dept_kind_idx",
            ),
        ]


class CourseEnrollment(TimeStampedModel):
    department = models.ForeignKey(
        Department, on_delete=models.CASCADE, related_name="course_enrollments"
    )
    course_code = models.CharField(max_length=32)
    faculty_user_id = models.IntegerField()
    student_user_id = models.IntegerField()
    academic_year = models.CharField(max_length=32, blank=True)

    class Meta:
        ordering = ["course_code", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["department", "course_code", "faculty_user_id", "student_user_id"],
                name="dept_enrollment_unique_pair",
            ),
        ]
        indexes = [
            models.Index(
                fields=["department", "faculty_user_id"],
                name="dept_enroll_faculty_idx",
            ),
        ]
