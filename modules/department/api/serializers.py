"""Wire shapes for the department's read endpoints."""
from rest_framework import serializers

from modules.department.models.departments import Department


class DepartmentSerializer(serializers.ModelSerializer):
    """Serializer for Department objects."""

    class Meta:
        model = Department
        fields = (
            "id",
            "code",
            "name",
            "core_policies",
            "about",
            "contact_email",
            "location",
            "website",
        )
