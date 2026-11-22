from rest_framework import serializers


class DepartmentReadSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    code = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)
    contact_email = serializers.EmailField(read_only=True, allow_blank=True)
    location = serializers.CharField(read_only=True)
    website_url = serializers.URLField(read_only=True, allow_blank=True)
    core_policies = serializers.CharField(read_only=True)
    active_hod_user_id = serializers.IntegerField(read_only=True, allow_null=True)
    active_dept_admin_user_id = serializers.IntegerField(read_only=True, allow_null=True)
    updated_at = serializers.DateTimeField(read_only=True)


class DepartmentGeneralUpdateSerializer(serializers.Serializer):
    description = serializers.CharField(required=False, allow_blank=True)
    contact_email = serializers.EmailField(required=False, allow_blank=True)
    location = serializers.CharField(required=False, allow_blank=True, max_length=160)
    website_url = serializers.URLField(required=False, allow_blank=True)


class OfficialChangeReadSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    department_id = serializers.IntegerField(read_only=True)
    field_name = serializers.CharField(read_only=True)
    previous_value = serializers.CharField(read_only=True)
    proposed_value = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    proposed_by_user_id = serializers.IntegerField(read_only=True)
    decided_by_user_id = serializers.IntegerField(read_only=True, allow_null=True)
    decided_at = serializers.DateTimeField(read_only=True, allow_null=True)
    decision_note = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)


class OfficialChangeCreateSerializer(serializers.Serializer):
    department_id = serializers.IntegerField()
    field_name = serializers.CharField(max_length=32)
    proposed_value = serializers.CharField()


class OfficialChangeDecideSerializer(serializers.Serializer):
    approve = serializers.BooleanField()
    note = serializers.CharField(required=False, allow_blank=True, default="", max_length=300)


class AnnouncementReadSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    department_id = serializers.IntegerField(read_only=True)
    title = serializers.CharField(read_only=True)
    content = serializers.CharField(read_only=True)
    target_roles = serializers.ListField(child=serializers.CharField(), read_only=True)
    target_programs = serializers.ListField(child=serializers.CharField(), read_only=True)
    target_academic_years = serializers.ListField(child=serializers.CharField(), read_only=True)
    status = serializers.CharField(read_only=True)
    created_by_user_id = serializers.IntegerField(read_only=True)
    updated_by_user_id = serializers.IntegerField(read_only=True, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)


class AnnouncementCreateSerializer(serializers.Serializer):
    department_id = serializers.IntegerField()
    title = serializers.CharField(max_length=200)
    content = serializers.CharField()
    target_roles = serializers.ListField(child=serializers.CharField())
    target_programs = serializers.ListField(
        child=serializers.CharField(), required=False, default=list
    )
    target_academic_years = serializers.ListField(
        child=serializers.CharField(), required=False, default=list
    )


class AnnouncementUpdateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200, required=False)
    content = serializers.CharField(required=False)
    target_roles = serializers.ListField(child=serializers.CharField(), required=False)
    target_programs = serializers.ListField(child=serializers.CharField(), required=False)
    target_academic_years = serializers.ListField(child=serializers.CharField(), required=False)


class InventoryItemReadSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    department_id = serializers.IntegerField(read_only=True)
    sku = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    category = serializers.CharField(read_only=True)
    unit = serializers.CharField(read_only=True)
    current_quantity = serializers.IntegerField(read_only=True)
    location = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class InventoryInsertSerializer(serializers.Serializer):
    department_id = serializers.IntegerField()
    sku = serializers.CharField(max_length=64)
    name = serializers.CharField(max_length=160)
    quantity = serializers.IntegerField(min_value=1)
    category = serializers.CharField(required=False, allow_blank=True, default="", max_length=80)
    unit = serializers.CharField(required=False, allow_blank=True, default="units", max_length=32)
    location = serializers.CharField(required=False, allow_blank=True, default="", max_length=160)
    description = serializers.CharField(required=False, allow_blank=True, default="")
    note = serializers.CharField(required=False, allow_blank=True, default="", max_length=300)


class StockRequestReadSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    department_id = serializers.IntegerField(read_only=True)
    item_id = serializers.IntegerField(read_only=True)
    item_name = serializers.CharField(source="item.name", read_only=True)
    item_sku = serializers.CharField(source="item.sku", read_only=True)
    requester_user_id = serializers.IntegerField(read_only=True)
    requested_quantity = serializers.IntegerField(read_only=True)
    purpose = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    hod_decided_by_user_id = serializers.IntegerField(read_only=True, allow_null=True)
    hod_decided_at = serializers.DateTimeField(read_only=True, allow_null=True)
    hod_note = serializers.CharField(read_only=True)
    issued_by_user_id = serializers.IntegerField(read_only=True, allow_null=True)
    issued_at = serializers.DateTimeField(read_only=True, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)


class StockRequestCreateSerializer(serializers.Serializer):
    item_id = serializers.IntegerField()
    requested_quantity = serializers.IntegerField(min_value=1)
    purpose = serializers.CharField(required=False, allow_blank=True, default="", max_length=300)


class StockRequestDecideSerializer(serializers.Serializer):
    approve = serializers.BooleanField()
    note = serializers.CharField(required=False, allow_blank=True, default="", max_length=300)


class StockRequestIssueSerializer(serializers.Serializer):
    note = serializers.CharField(required=False, allow_blank=True, default="", max_length=300)


class StockMovementReadSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    department_id = serializers.IntegerField(read_only=True)
    item_id = serializers.IntegerField(read_only=True)
    item_sku = serializers.CharField(source="item.sku", read_only=True)
    item_name = serializers.CharField(source="item.name", read_only=True)
    stock_request_id = serializers.IntegerField(read_only=True, allow_null=True)
    movement_type = serializers.CharField(read_only=True)
    quantity_delta = serializers.IntegerField(read_only=True)
    balance_after = serializers.IntegerField(read_only=True)
    actor_user_id = serializers.IntegerField(read_only=True)
    note = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)


class FeedbackReadSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    department_id = serializers.IntegerField(read_only=True)
    submitter_user_id = serializers.IntegerField(read_only=True)
    submitter_role = serializers.CharField(read_only=True)
    subject = serializers.CharField(read_only=True)
    body = serializers.CharField(read_only=True)
    category = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    initial_reviewed_by_user_id = serializers.IntegerField(read_only=True, allow_null=True)
    initial_reviewed_at = serializers.DateTimeField(read_only=True, allow_null=True)
    resolved_by_user_id = serializers.IntegerField(read_only=True, allow_null=True)
    resolved_at = serializers.DateTimeField(read_only=True, allow_null=True)
    resolution_note = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)


class FeedbackCreateSerializer(serializers.Serializer):
    department_id = serializers.IntegerField()
    subject = serializers.CharField(max_length=200)
    body = serializers.CharField()


class FeedbackReviewSerializer(serializers.Serializer):
    category = serializers.CharField(max_length=80)
    close_as_simple = serializers.BooleanField(required=False, default=False)
    note = serializers.CharField(required=False, allow_blank=True, default="", max_length=300)


class FeedbackDisposeSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=["resolved", "closed"])
    note = serializers.CharField(required=False, allow_blank=True, default="", max_length=300)


class TimetableSlotReadSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    department_id = serializers.IntegerField(read_only=True)
    slot_kind = serializers.CharField(read_only=True)
    program = serializers.CharField(read_only=True)
    academic_year = serializers.CharField(read_only=True)
    section = serializers.CharField(read_only=True)
    course_code = serializers.CharField(read_only=True)
    course_title = serializers.CharField(read_only=True)
    faculty_user_id = serializers.IntegerField(read_only=True, allow_null=True)
    room = serializers.CharField(read_only=True)
    day_of_week = serializers.IntegerField(read_only=True)
    start_time = serializers.TimeField(read_only=True)
    end_time = serializers.TimeField(read_only=True)


class TimetableSlotCreateSerializer(serializers.Serializer):
    department_id = serializers.IntegerField()
    slot_kind = serializers.ChoiceField(choices=["class", "lab"], default="class")
    program = serializers.CharField(max_length=64)
    academic_year = serializers.CharField(max_length=32)
    section = serializers.CharField(max_length=32, required=False, default="A")
    course_code = serializers.CharField(max_length=32)
    course_title = serializers.CharField(max_length=160)
    faculty_user_id = serializers.IntegerField(required=False, allow_null=True, default=None)
    room = serializers.CharField(max_length=64)
    day_of_week = serializers.IntegerField(min_value=0, max_value=6)
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()


class TimetableSlotUpdateSerializer(serializers.Serializer):
    slot_kind = serializers.ChoiceField(choices=["class", "lab"], required=False)
    program = serializers.CharField(max_length=64, required=False)
    academic_year = serializers.CharField(max_length=32, required=False)
    section = serializers.CharField(max_length=32, required=False)
    course_code = serializers.CharField(max_length=32, required=False)
    course_title = serializers.CharField(max_length=160, required=False)
    faculty_user_id = serializers.IntegerField(required=False, allow_null=True)
    room = serializers.CharField(max_length=64, required=False)
    day_of_week = serializers.IntegerField(min_value=0, max_value=6, required=False)
    start_time = serializers.TimeField(required=False)
    end_time = serializers.TimeField(required=False)
    is_active = serializers.BooleanField(required=False)


class LabResourceReadSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    department_id = serializers.IntegerField(read_only=True)
    lab_code = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    location = serializers.CharField(read_only=True)
    equipment_summary = serializers.CharField(read_only=True)
    capacity = serializers.IntegerField(read_only=True)
    status = serializers.CharField(read_only=True)
    incharge_user_id = serializers.IntegerField(read_only=True, allow_null=True)
    updated_at = serializers.DateTimeField(read_only=True)


class LabResourceWriteSerializer(serializers.Serializer):
    department_id = serializers.IntegerField(required=False)
    lab_code = serializers.CharField(max_length=32, required=False, default="")
    name = serializers.CharField(max_length=160)
    location = serializers.CharField(required=False, allow_blank=True, default="", max_length=160)
    equipment_summary = serializers.CharField(required=False, allow_blank=True, default="")
    capacity = serializers.IntegerField(min_value=0, required=False, default=0)
    status = serializers.ChoiceField(
        choices=["operational", "maintenance", "decommissioned"],
        required=False,
        default="operational",
    )
    incharge_user_id = serializers.IntegerField(required=False, allow_null=True, default=None)


class DepartmentProgramReadSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    department_id = serializers.IntegerField(read_only=True)
    code = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    degree_level = serializers.CharField(read_only=True)
    duration_years = serializers.IntegerField(read_only=True)
    description = serializers.CharField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)


class DepartmentProgramWriteSerializer(serializers.Serializer):
    department_id = serializers.IntegerField(required=False)
    code = serializers.CharField(max_length=32, required=False, default="")
    name = serializers.CharField(max_length=160)
    degree_level = serializers.CharField(max_length=64, required=False, default="UG")
    duration_years = serializers.IntegerField(min_value=1, max_value=10, required=False, default=4)
    description = serializers.CharField(required=False, allow_blank=True, default="")
    is_active = serializers.BooleanField(required=False, default=True)


class DepartmentProfileReadSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    department_id = serializers.IntegerField(read_only=True)
    user_id = serializers.IntegerField(read_only=True)
    profile_kind = serializers.CharField(read_only=True)
    display_name = serializers.CharField(read_only=True)
    program = serializers.CharField(read_only=True)
    visibility_tier = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True, required=False, allow_blank=True)
    academic_year = serializers.CharField(read_only=True, required=False, allow_blank=True)
    designation_title = serializers.CharField(read_only=True, required=False, allow_blank=True)
    office_room = serializers.CharField(read_only=True, required=False, allow_blank=True)
    research_area = serializers.CharField(read_only=True, required=False, allow_blank=True)
    graduation_year = serializers.IntegerField(read_only=True, required=False, allow_null=True)
    current_affiliation = serializers.CharField(read_only=True, required=False, allow_blank=True)
    academic_notes = serializers.CharField(read_only=True, required=False, allow_blank=True)


class DepartmentProfileWriteSerializer(serializers.Serializer):
    department_id = serializers.IntegerField(required=False)
    user_id = serializers.IntegerField(required=False)
    profile_kind = serializers.ChoiceField(
        choices=["student", "faculty", "alumni"], required=False, default="student"
    )
    display_name = serializers.CharField(max_length=160)
    email = serializers.EmailField(required=False, allow_blank=True, default="")
    program = serializers.CharField(max_length=64, required=False, allow_blank=True, default="")
    academic_year = serializers.CharField(
        max_length=32, required=False, allow_blank=True, default=""
    )
    designation_title = serializers.CharField(
        max_length=120, required=False, allow_blank=True, default=""
    )
    office_room = serializers.CharField(max_length=64, required=False, allow_blank=True, default="")
    research_area = serializers.CharField(
        max_length=200, required=False, allow_blank=True, default=""
    )
    graduation_year = serializers.IntegerField(required=False, allow_null=True, default=None)
    current_affiliation = serializers.CharField(
        max_length=160, required=False, allow_blank=True, default=""
    )
    academic_notes = serializers.CharField(required=False, allow_blank=True, default="")


class CourseEnrollmentReadSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    department_id = serializers.IntegerField(read_only=True)
    course_code = serializers.CharField(read_only=True)
    faculty_user_id = serializers.IntegerField(read_only=True)
    student_user_id = serializers.IntegerField(read_only=True)
    academic_year = serializers.CharField(read_only=True)


class CourseEnrollmentCreateSerializer(serializers.Serializer):
    department_id = serializers.IntegerField()
    course_code = serializers.CharField(max_length=32)
    faculty_user_id = serializers.IntegerField()
    student_user_id = serializers.IntegerField()
    academic_year = serializers.CharField(
        max_length=32, required=False, allow_blank=True, default=""
    )


class RoleAssignmentReadSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    department_id = serializers.IntegerField(read_only=True)
    role_type = serializers.CharField(read_only=True)
    user_id = serializers.IntegerField(read_only=True)
    valid_from = serializers.DateTimeField(read_only=True)
    valid_to = serializers.DateTimeField(read_only=True)
    status = serializers.CharField(read_only=True)
    assigned_by_user_id = serializers.IntegerField(read_only=True)
    activated_at = serializers.DateTimeField(read_only=True, allow_null=True)
    revoked_at = serializers.DateTimeField(read_only=True, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)


class RoleAssignmentCreateSerializer(serializers.Serializer):
    department_id = serializers.IntegerField()
    role_type = serializers.ChoiceField(choices=["hod", "dept_admin"])
    user_id = serializers.IntegerField()
    valid_from = serializers.DateTimeField()
    valid_to = serializers.DateTimeField()
