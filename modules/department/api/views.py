from __future__ import annotations

from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.api.exceptions import BadRequestError, NotFoundError
from core.api.pagination import CursorPagination
from fusion_auth.permissions import HasModuleGrant, HasPermission
from modules.department.api import serializers as s
from modules.department.selectors import profiles as profile_selectors
from modules.department.selectors import scoping
from modules.department.services import (
    announcements as announcement_svc,
)
from modules.department.services import (
    department as dept_svc,
)
from modules.department.services import (
    feedback as feedback_svc,
)
from modules.department.services import (
    inventory as inventory_svc,
)
from modules.department.services import (
    profiles as profile_svc,
)
from modules.department.services import (
    resources as resource_svc,
)
from modules.department.services import (
    roles as role_svc,
)


def _int_param(request, name: str) -> int | None:
    raw = request.query_params.get(name)
    if raw is None or raw == "":
        return None
    try:
        return int(raw)
    except ValueError as exc:
        raise BadRequestError(
            f"Query parameter {name!r} must be an integer.", code="invalid_query_param"
        ) from exc


def _paginate(request, qs, serializer_cls, view):
    paginator = CursorPagination()
    page = paginator.paginate_queryset(qs, request, view=view)
    return paginator.get_paginated_response(serializer_cls(page, many=True).data)


# -- Departments and Official Changes -----------------------------------------
class DepartmentListView(APIView):
    permission_classes = [
        HasModuleGrant("department"),
        HasPermission("department.department.view"),
    ]

    @extend_schema(
        summary="List departments visible to the caller",
        tags=["department"],
        responses=s.DepartmentReadSerializer(many=True),
        examples=[
            OpenApiExample(
                "department_list",
                value={"next": None, "previous": None, "results": [{"id": 1, "code": "CSE"}]},
                response_only=True,
            )
        ],
    )
    def get(self, request):
        return _paginate(request, scoping.departments_for(request.principal),
                         s.DepartmentReadSerializer, self)


class DepartmentDetailView(APIView):
    throttle_scope = "dept_write"

    def get_permissions(self):
        perm = (
            "department.department.update"
            if self.request.method == "PATCH"
            else "department.department.view"
        )
        return [HasModuleGrant("department")(), HasPermission(perm)()]

    @extend_schema(
        summary="Retrieve a department record",
        tags=["department"],
        responses=s.DepartmentReadSerializer,
        examples=[OpenApiExample("dept", value={"id": 1, "code": "CSE"}, response_only=True)],
    )
    def get(self, request, pk: int):
        dept = scoping.departments_for(request.principal).filter(pk=pk).first()
        if dept is None:
            raise NotFoundError("Department not found.", code="department_not_found")
        return Response(s.DepartmentReadSerializer(dept).data)

    @extend_schema(
        summary="Update general non-official department information",
        tags=["department"],
        request=s.DepartmentGeneralUpdateSerializer,
        responses=s.DepartmentReadSerializer,
        examples=[
            OpenApiExample(
                "update_general",
                value={"description": "Department of CSE", "location": "Core Lab Complex"},
                request_only=True,
            )
        ],
    )
    def patch(self, request, pk: int):
        ser = s.DepartmentGeneralUpdateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        dept = dept_svc.update_general_details(
            department_id=pk, actor=request.principal, **ser.validated_data
        )
        return Response(s.DepartmentReadSerializer(dept).data)


class OfficialChangeListCreateView(APIView):
    throttle_scope = "dept_write"

    def get_permissions(self):
        perm = (
            "department.department.update"
            if self.request.method == "POST"
            else "department.official_change.view"
        )
        return [HasModuleGrant("department")(), HasPermission(perm)()]

    @extend_schema(
        summary="List official department-detail change requests",
        tags=["department"],
        responses=s.OfficialChangeReadSerializer(many=True),
        examples=[OpenApiExample("changes", value={"results": []}, response_only=True)],
    )
    def get(self, request):
        qs = scoping.official_changes_for(request.principal)
        dept_id = _int_param(request, "department")
        if dept_id is not None:
            qs = qs.filter(department_id=dept_id)
        return _paginate(request, qs, s.OfficialChangeReadSerializer, self)

    @extend_schema(
        summary="Propose an official department-detail change for HOD approval",
        tags=["department"],
        request=s.OfficialChangeCreateSerializer,
        responses={201: s.OfficialChangeReadSerializer},
        examples=[
            OpenApiExample(
                "propose_change",
                value={"department_id": 1, "field_name": "core_policies",
                       "proposed_value": "Updated lab safety policy"},
                request_only=True,
            )
        ],
    )
    def post(self, request):
        ser = s.OfficialChangeCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        change = dept_svc.propose_official_change(
            actor=request.principal, **ser.validated_data
        )
        return Response(s.OfficialChangeReadSerializer(change).data, status=status.HTTP_201_CREATED)


class OfficialChangeDecideView(APIView):
    throttle_scope = "dept_write"
    permission_classes = [
        HasModuleGrant("department"),
        HasPermission("department.official_change.approve"),
    ]

    @extend_schema(
        summary="Approve or reject a pending official department-detail change",
        tags=["department"],
        request=s.OfficialChangeDecideSerializer,
        responses=s.OfficialChangeReadSerializer,
        examples=[
            OpenApiExample(
                "approve_change", value={"approve": True, "note": "Approved"}, request_only=True
            )
        ],
    )
    def post(self, request, pk: int):
        ser = s.OfficialChangeDecideSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        change = dept_svc.decide_official_change(
            change_id=pk, actor=request.principal, **ser.validated_data
        )
        return Response(s.OfficialChangeReadSerializer(change).data)


# -- Announcements ------------------------------------------------------------
class AnnouncementListCreateView(APIView):
    throttle_scope = "dept_write"

    def get_permissions(self):
        perm = (
            "department.announcement.create"
            if self.request.method == "POST"
            else "department.announcement.view"
        )
        return [HasModuleGrant("department")(), HasPermission(perm)()]

    @extend_schema(
        summary="List relevant department announcements",
        tags=["department"],
        responses=s.AnnouncementReadSerializer(many=True),
        examples=[OpenApiExample("announcements", value={"results": []}, response_only=True)],
    )
    def get(self, request):
        qs = scoping.announcements_for(request.principal)
        dept_id = _int_param(request, "department")
        if dept_id is not None:
            qs = qs.filter(department_id=dept_id)
        return _paginate(request, qs, s.AnnouncementReadSerializer, self)

    @extend_schema(
        summary="Create and publish a targeted department announcement",
        tags=["department"],
        request=s.AnnouncementCreateSerializer,
        responses={201: s.AnnouncementReadSerializer},
        examples=[
            OpenApiExample(
                "create_ann",
                value={
                    "department_id": 1,
                    "title": "Mid-sem lab schedule",
                    "content": "Labs start Monday.",
                    "target_roles": ["student", "faculty"],
                },
                request_only=True,
            )
        ],
    )
    def post(self, request):
        ser = s.AnnouncementCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        ann = announcement_svc.create_announcement(actor=request.principal, **ser.validated_data)
        return Response(s.AnnouncementReadSerializer(ann).data, status=status.HTTP_201_CREATED)


class AnnouncementDetailView(APIView):
    throttle_scope = "dept_write"

    def get_permissions(self):
        if self.request.method == "PATCH":
            perm = "department.announcement.update"
        elif self.request.method == "DELETE":
            perm = "department.announcement.delete"
        else:
            perm = "department.announcement.view"
        return [HasModuleGrant("department")(), HasPermission(perm)()]

    @extend_schema(
        summary="Retrieve a single relevant announcement",
        tags=["department"],
        responses=s.AnnouncementReadSerializer,
        examples=[OpenApiExample("ann", value={"id": 1, "title": "Notice"}, response_only=True)],
    )
    def get(self, request, pk: int):
        ann = scoping.announcements_for(request.principal).filter(pk=pk).first()
        if ann is None:
            raise NotFoundError("Announcement not found.", code="announcement_not_found")
        return Response(s.AnnouncementReadSerializer(ann).data)

    @extend_schema(
        summary="Edit an active department announcement (HOD)",
        tags=["department"],
        request=s.AnnouncementUpdateSerializer,
        responses=s.AnnouncementReadSerializer,
        examples=[OpenApiExample("edit_ann", value={"title": "Updated title"}, request_only=True)],
    )
    def patch(self, request, pk: int):
        ser = s.AnnouncementUpdateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        ann = announcement_svc.update_announcement(
            announcement_id=pk, actor=request.principal, **ser.validated_data
        )
        return Response(s.AnnouncementReadSerializer(ann).data)

    @extend_schema(
        summary="Delete an active department announcement (HOD)",
        tags=["department"],
        responses={204: None},
        examples=[OpenApiExample("del_ann", value=None, response_only=True)],
    )
    def delete(self, request, pk: int):
        announcement_svc.delete_announcement(announcement_id=pk, actor=request.principal)
        return Response(status=status.HTTP_204_NO_CONTENT)


class AnnouncementHideView(APIView):
    throttle_scope = "dept_write"
    permission_classes = [
        HasModuleGrant("department"),
        HasPermission("department.announcement.update"),
    ]

    @extend_schema(
        summary="Hide an active department announcement (HOD)",
        tags=["department"],
        request=None,
        responses=s.AnnouncementReadSerializer,
        examples=[OpenApiExample("hide_ann", value={"id": 1, "status": "hidden"},
                                 response_only=True)],
    )
    def post(self, request, pk: int):
        ann = announcement_svc.hide_announcement(announcement_id=pk, actor=request.principal)
        return Response(s.AnnouncementReadSerializer(ann).data)


# -- Inventory & Stock Requests -----------------------------------------------
class InventoryListCreateView(APIView):
    throttle_scope = "dept_write"

    def get_permissions(self):
        perm = (
            "department.inventory.create"
            if self.request.method == "POST"
            else "department.inventory.view"
        )
        return [HasModuleGrant("department")(), HasPermission(perm)()]

    @extend_schema(
        summary="List department inventory items",
        tags=["department"],
        responses=s.InventoryItemReadSerializer(many=True),
        examples=[OpenApiExample("inv_list", value={"results": []}, response_only=True)],
    )
    def get(self, request):
        qs = scoping.inventory_for(request.principal)
        dept_id = _int_param(request, "department")
        if dept_id is not None:
            qs = qs.filter(department_id=dept_id)
        return _paginate(request, qs, s.InventoryItemReadSerializer, self)

    @extend_schema(
        summary="Insert stock into department inventory (Dept_Admin)",
        tags=["department"],
        request=s.InventoryInsertSerializer,
        responses={201: s.InventoryItemReadSerializer},
        examples=[
            OpenApiExample(
                "insert_stock",
                value={"department_id": 1, "sku": "HDMI-01", "name": "HDMI Cable", "quantity": 10},
                request_only=True,
            )
        ],
    )
    def post(self, request):
        ser = s.InventoryInsertSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        item = inventory_svc.insert_stock(actor=request.principal, **ser.validated_data)
        return Response(s.InventoryItemReadSerializer(item).data, status=status.HTTP_201_CREATED)


class StockRequestListCreateView(APIView):
    throttle_scope = "dept_write"

    def get_permissions(self):
        perm = (
            "department.stock_request.create"
            if self.request.method == "POST"
            else "department.stock_request.view"
        )
        return [HasModuleGrant("department")(), HasPermission(perm)()]

    @extend_schema(
        summary="List stock requests within caller scope",
        tags=["department"],
        responses=s.StockRequestReadSerializer(many=True),
        examples=[OpenApiExample("sr_list", value={"results": []}, response_only=True)],
    )
    def get(self, request):
        qs = scoping.stock_requests_for(request.principal)
        dept_id = _int_param(request, "department")
        if dept_id is not None:
            qs = qs.filter(department_id=dept_id)
        st = request.query_params.get("status")
        if st:
            qs = qs.filter(status=st)
        return _paginate(request, qs, s.StockRequestReadSerializer, self)

    @extend_schema(
        summary="Submit a Faculty stock request",
        tags=["department"],
        request=s.StockRequestCreateSerializer,
        responses={201: s.StockRequestReadSerializer},
        examples=[
            OpenApiExample(
                "req_stock",
                value={"item_id": 1, "requested_quantity": 2, "purpose": "Lab practicals"},
                request_only=True,
            )
        ],
    )
    def post(self, request):
        ser = s.StockRequestCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        req = inventory_svc.request_stock(actor=request.principal, **ser.validated_data)
        return Response(s.StockRequestReadSerializer(req).data, status=status.HTTP_201_CREATED)


class StockRequestDecideView(APIView):
    throttle_scope = "dept_write"
    permission_classes = [
        HasModuleGrant("department"),
        HasPermission("department.stock_request.approve"),
    ]

    @extend_schema(
        summary="Approve or reject a pending Faculty stock request (HOD)",
        tags=["department"],
        request=s.StockRequestDecideSerializer,
        responses=s.StockRequestReadSerializer,
        examples=[OpenApiExample("decide", value={"approve": True, "note": "OK"},
                                 request_only=True)],
    )
    def post(self, request, pk: int):
        ser = s.StockRequestDecideSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        req = inventory_svc.decide_stock_request(
            request_id=pk, actor=request.principal, **ser.validated_data
        )
        return Response(s.StockRequestReadSerializer(req).data)


class StockRequestIssueView(APIView):
    throttle_scope = "dept_write"
    permission_classes = [
        HasModuleGrant("department"),
        HasPermission("department.stock_request.update"),
    ]

    @extend_schema(
        summary="Issue stock for a HOD-approved request (Dept_Admin)",
        tags=["department"],
        request=s.StockRequestIssueSerializer,
        responses=s.StockRequestReadSerializer,
        examples=[OpenApiExample("issue", value={"note": "Issued from store"}, request_only=True)],
    )
    def post(self, request, pk: int):
        ser = s.StockRequestIssueSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        req = inventory_svc.issue_stock(
            request_id=pk, actor=request.principal, **ser.validated_data
        )
        return Response(s.StockRequestReadSerializer(req).data)


class StockMovementListView(APIView):
    permission_classes = [
        HasModuleGrant("department"),
        HasPermission("department.stock_movement.view"),
    ]

    @extend_schema(
        summary="List immutable stock movement history within caller scope",
        tags=["department"],
        responses=s.StockMovementReadSerializer(many=True),
        examples=[OpenApiExample("movements", value={"results": []}, response_only=True)],
    )
    def get(self, request):
        qs = scoping.stock_movements_for(request.principal)
        dept_id = _int_param(request, "department")
        if dept_id is not None:
            qs = qs.filter(department_id=dept_id)
        return _paginate(request, qs, s.StockMovementReadSerializer, self)


# -- Feedback -----------------------------------------------------------------
class FeedbackListCreateView(APIView):
    throttle_scope = "dept_feedback"

    def get_permissions(self):
        perm = (
            "department.feedback.create"
            if self.request.method == "POST"
            else "department.feedback.view"
        )
        return [HasModuleGrant("department")(), HasPermission(perm)()]

    @extend_schema(
        summary="List confidential feedback visible to caller",
        tags=["department"],
        responses=s.FeedbackReadSerializer(many=True),
        examples=[OpenApiExample("fb_list", value={"results": []}, response_only=True)],
    )
    def get(self, request):
        qs = scoping.feedback_for(request.principal)
        dept_id = _int_param(request, "department")
        if dept_id is not None:
            qs = qs.filter(department_id=dept_id)
        return _paginate(request, qs, s.FeedbackReadSerializer, self)

    @extend_schema(
        summary="Submit confidential department feedback (Student or Faculty)",
        tags=["department"],
        request=s.FeedbackCreateSerializer,
        responses={201: s.FeedbackReadSerializer},
        examples=[
            OpenApiExample(
                "submit_fb",
                value={"department_id": 1, "subject": "Lab projector",
                       "body": "Projector in L-204 flickers."},
                request_only=True,
            )
        ],
    )
    def post(self, request):
        ser = s.FeedbackCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        fb = feedback_svc.submit_feedback(actor=request.principal, **ser.validated_data)
        return Response(s.FeedbackReadSerializer(fb).data, status=status.HTTP_201_CREATED)


class FeedbackReviewView(APIView):
    throttle_scope = "dept_write"
    permission_classes = [
        HasModuleGrant("department"),
        HasPermission("department.feedback.review"),
    ]

    @extend_schema(
        summary="Perform initial review and categorization of new feedback (Dept_Admin)",
        tags=["department"],
        request=s.FeedbackReviewSerializer,
        responses=s.FeedbackReadSerializer,
        examples=[
            OpenApiExample(
                "review_fb",
                value={"category": "Infrastructure", "close_as_simple": False, "note": "Logged"},
                request_only=True,
            )
        ],
    )
    def post(self, request, pk: int):
        ser = s.FeedbackReviewSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        fb = feedback_svc.review_feedback(
            feedback_id=pk, actor=request.principal, **ser.validated_data
        )
        return Response(s.FeedbackReadSerializer(fb).data)


class FeedbackDisposeView(APIView):
    throttle_scope = "dept_write"
    permission_classes = [
        HasModuleGrant("department"),
        HasPermission("department.feedback.update"),
    ]

    @extend_schema(
        summary="Resolve or close reviewed feedback (Dept_Admin or HOD)",
        tags=["department"],
        request=s.FeedbackDisposeSerializer,
        responses=s.FeedbackReadSerializer,
        examples=[
            OpenApiExample(
                "dispose_fb",
                value={"status": "resolved", "note": "Projector bulb replaced."},
                request_only=True,
            )
        ],
    )
    def post(self, request, pk: int):
        ser = s.FeedbackDisposeSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        fb = feedback_svc.dispose_feedback(
            feedback_id=pk, actor=request.principal, **ser.validated_data
        )
        return Response(s.FeedbackReadSerializer(fb).data)


# -- Timetables, Labs, and Academic Programs ----------------------------------
class TimetableListCreateView(APIView):
    throttle_scope = "dept_write"

    def get_permissions(self):
        perm = (
            "department.timetable.create"
            if self.request.method == "POST"
            else "department.timetable.view"
        )
        return [HasModuleGrant("department")(), HasPermission(perm)()]

    @extend_schema(
        summary="List active class and lab timetable slots",
        tags=["department"],
        responses=s.TimetableSlotReadSerializer(many=True),
        examples=[OpenApiExample("tt_list", value={"results": []}, response_only=True)],
    )
    def get(self, request):
        qs = scoping.timetables_for(request.principal)
        dept_id = _int_param(request, "department")
        if dept_id is not None:
            qs = qs.filter(department_id=dept_id)
        day = _int_param(request, "day_of_week")
        if day is not None:
            qs = qs.filter(day_of_week=day)
        program = request.query_params.get("program")
        if program:
            qs = qs.filter(program__iexact=program)
        return _paginate(request, qs, s.TimetableSlotReadSerializer, self)

    @extend_schema(
        summary="Upload a conflict-free timetable slot (Dept_Admin)",
        tags=["department"],
        request=s.TimetableSlotCreateSerializer,
        responses={201: s.TimetableSlotReadSerializer},
        examples=[
            OpenApiExample(
                "create_slot",
                value={
                    "department_id": 1,
                    "slot_kind": "class",
                    "program": "BTech",
                    "academic_year": "2026-27",
                    "section": "A",
                    "course_code": "CS201",
                    "course_title": "Data Structures",
                    "room": "L-101",
                    "day_of_week": 1,
                    "start_time": "09:00:00",
                    "end_time": "10:00:00",
                },
                request_only=True,
            )
        ],
    )
    def post(self, request):
        ser = s.TimetableSlotCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        slot = resource_svc.create_timetable_slot(actor=request.principal, **ser.validated_data)
        return Response(s.TimetableSlotReadSerializer(slot).data, status=status.HTTP_201_CREATED)


class TimetableDetailView(APIView):
    throttle_scope = "dept_write"
    permission_classes = [
        HasModuleGrant("department"),
        HasPermission("department.timetable.update"),
    ]

    @extend_schema(
        summary="Modify an existing timetable slot with conflict validation (Dept_Admin)",
        tags=["department"],
        request=s.TimetableSlotUpdateSerializer,
        responses=s.TimetableSlotReadSerializer,
        examples=[OpenApiExample("upd_slot", value={"room": "L-102"}, request_only=True)],
    )
    def patch(self, request, pk: int):
        ser = s.TimetableSlotUpdateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        slot = resource_svc.update_timetable_slot(
            slot_id=pk, actor=request.principal, **ser.validated_data
        )
        return Response(s.TimetableSlotReadSerializer(slot).data)


class LabResourceListCreateView(APIView):
    throttle_scope = "dept_write"

    def get_permissions(self):
        perm = (
            "department.lab.update"
            if self.request.method == "POST"
            else "department.lab.view"
        )
        return [HasModuleGrant("department")(), HasPermission(perm)()]

    @extend_schema(
        summary="List department lab equipment and resource profiles",
        tags=["department"],
        responses=s.LabResourceReadSerializer(many=True),
        examples=[OpenApiExample("labs", value={"results": []}, response_only=True)],
    )
    def get(self, request):
        qs = scoping.lab_resources_for(request.principal)
        dept_id = _int_param(request, "department")
        if dept_id is not None:
            qs = qs.filter(department_id=dept_id)
        return _paginate(request, qs, s.LabResourceReadSerializer, self)

    @extend_schema(
        summary="Create a lab equipment/resource profile (Dept_Admin)",
        tags=["department"],
        request=s.LabResourceWriteSerializer,
        responses={201: s.LabResourceReadSerializer},
        examples=[
            OpenApiExample(
                "create_lab",
                value={"department_id": 1, "lab_code": "CSE-ML1", "name": "AI & ML Lab",
                       "capacity": 40},
                request_only=True,
            )
        ],
    )
    def post(self, request):
        ser = s.LabResourceWriteSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        lab = resource_svc.create_or_update_lab(actor=request.principal, **ser.validated_data)
        return Response(s.LabResourceReadSerializer(lab).data, status=status.HTTP_201_CREATED)


class LabResourceDetailView(APIView):
    throttle_scope = "dept_write"
    permission_classes = [
        HasModuleGrant("department"),
        HasPermission("department.lab.update"),
    ]

    @extend_schema(
        summary="Update a lab equipment/resource profile (Dept_Admin)",
        tags=["department"],
        request=s.LabResourceWriteSerializer,
        responses=s.LabResourceReadSerializer,
        examples=[OpenApiExample("upd_lab", value={"name": "AI Lab", "capacity": 45},
                                 request_only=True)],
    )
    def patch(self, request, pk: int):
        ser = s.LabResourceWriteSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        lab = resource_svc.create_or_update_lab(
            actor=request.principal, lab_id=pk, **ser.validated_data
        )
        return Response(s.LabResourceReadSerializer(lab).data)


class ProgramListCreateView(APIView):
    throttle_scope = "dept_write"

    def get_permissions(self):
        perm = (
            "department.program.update"
            if self.request.method == "POST"
            else "department.program.view"
        )
        return [HasModuleGrant("department")(), HasPermission(perm)()]

    @extend_schema(
        summary="List department academic programs",
        tags=["department"],
        responses=s.DepartmentProgramReadSerializer(many=True),
        examples=[OpenApiExample("programs", value={"results": []}, response_only=True)],
    )
    def get(self, request):
        qs = scoping.programs_for(request.principal)
        dept_id = _int_param(request, "department")
        if dept_id is not None:
            qs = qs.filter(department_id=dept_id)
        return _paginate(request, qs, s.DepartmentProgramReadSerializer, self)

    @extend_schema(
        summary="Create a department academic program (Dept_Admin)",
        tags=["department"],
        request=s.DepartmentProgramWriteSerializer,
        responses={201: s.DepartmentProgramReadSerializer},
        examples=[
            OpenApiExample(
                "create_prog",
                value={"department_id": 1, "code": "BTECH-CSE", "name": "B.Tech CSE",
                       "degree_level": "UG", "duration_years": 4},
                request_only=True,
            )
        ],
    )
    def post(self, request):
        ser = s.DepartmentProgramWriteSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        prog = resource_svc.create_or_update_program(actor=request.principal, **ser.validated_data)
        return Response(
            s.DepartmentProgramReadSerializer(prog).data, status=status.HTTP_201_CREATED
        )


class ProgramDetailView(APIView):
    throttle_scope = "dept_write"
    permission_classes = [
        HasModuleGrant("department"),
        HasPermission("department.program.update"),
    ]

    @extend_schema(
        summary="Update a department academic program (Dept_Admin)",
        tags=["department"],
        request=s.DepartmentProgramWriteSerializer,
        responses=s.DepartmentProgramReadSerializer,
        examples=[OpenApiExample("upd_prog", value={"name": "B.Tech CSE (Hons)"},
                                 request_only=True)],
    )
    def patch(self, request, pk: int):
        ser = s.DepartmentProgramWriteSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        prog = resource_svc.create_or_update_program(
            actor=request.principal, program_id=pk, **ser.validated_data
        )
        return Response(s.DepartmentProgramReadSerializer(prog).data)


# -- Profiles & Course Roster -------------------------------------------------
class ProfileListCreateView(APIView):
    throttle_scope = "dept_write"

    def get_permissions(self):
        perm = (
            "department.profile.update"
            if self.request.method == "POST"
            else "department.profile.view"
        )
        return [HasModuleGrant("department")(), HasPermission(perm)()]

    @extend_schema(
        summary="List department user profiles projected for caller visibility scope",
        tags=["department"],
        responses=s.DepartmentProfileReadSerializer(many=True),
        examples=[OpenApiExample("profiles", value={"results": []}, response_only=True)],
    )
    def get(self, request):
        dept_id = _int_param(request, "department")
        kind = request.query_params.get("profile_kind") or None
        rows = profile_selectors.list_visible_profiles(
            request.principal, department_id=dept_id, profile_kind=kind
        )
        return Response({"results": rows})

    @extend_schema(
        summary="Create a department user profile (Dept_Admin)",
        tags=["department"],
        request=s.DepartmentProfileWriteSerializer,
        responses={201: s.DepartmentProfileReadSerializer},
        examples=[
            OpenApiExample(
                "create_prof",
                value={"department_id": 1, "user_id": 1001, "profile_kind": "student",
                       "display_name": "Asha Verma", "program": "BTech", "academic_year": "2026"},
                request_only=True,
            )
        ],
    )
    def post(self, request):
        ser = s.DepartmentProfileWriteSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        prof = profile_svc.upsert_profile(actor=request.principal, **ser.validated_data)
        projected = profile_selectors.get_visible_profile(request.principal, prof.pk)
        return Response(projected, status=status.HTTP_201_CREATED)


class ProfileDetailView(APIView):
    throttle_scope = "dept_write"

    def get_permissions(self):
        perm = (
            "department.profile.update"
            if self.request.method == "PATCH"
            else "department.profile.view"
        )
        return [HasModuleGrant("department")(), HasPermission(perm)()]

    @extend_schema(
        summary="Retrieve a department user profile projected for caller visibility scope",
        tags=["department"],
        responses=s.DepartmentProfileReadSerializer,
        examples=[OpenApiExample("prof", value={"id": 1, "display_name": "Asha"},
                                 response_only=True)],
    )
    def get(self, request, pk: int):
        projected = profile_selectors.get_visible_profile(request.principal, pk)
        if projected is None:
            raise NotFoundError("Department profile not found.", code="profile_not_found")
        return Response(projected)

    @extend_schema(
        summary="Update a department user profile (Dept_Admin)",
        tags=["department"],
        request=s.DepartmentProfileWriteSerializer,
        responses=s.DepartmentProfileReadSerializer,
        examples=[OpenApiExample("upd_prof", value={"display_name": "Asha V."}, request_only=True)],
    )
    def patch(self, request, pk: int):
        ser = s.DepartmentProfileWriteSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        prof = profile_svc.upsert_profile(
            actor=request.principal, profile_id=pk, **ser.validated_data
        )
        projected = profile_selectors.get_visible_profile(request.principal, prof.pk)
        return Response(projected)


class RosterListCreateView(APIView):
    throttle_scope = "dept_write"

    def get_permissions(self):
        perm = (
            "department.roster.update"
            if self.request.method == "POST"
            else "department.profile.view"
        )
        return [HasModuleGrant("department")(), HasPermission(perm)()]

    @extend_schema(
        summary="List course enrollments within caller scope",
        tags=["department"],
        responses=s.CourseEnrollmentReadSerializer(many=True),
        examples=[OpenApiExample("roster", value={"results": []}, response_only=True)],
    )
    def get(self, request):
        qs = scoping.enrollments_for(request.principal)
        dept_id = _int_param(request, "department")
        if dept_id is not None:
            qs = qs.filter(department_id=dept_id)
        return _paginate(request, qs, s.CourseEnrollmentReadSerializer, self)

    @extend_schema(
        summary="Register a Faculty-Student course enrollment link (Dept_Admin)",
        tags=["department"],
        request=s.CourseEnrollmentCreateSerializer,
        responses={201: s.CourseEnrollmentReadSerializer},
        examples=[
            OpenApiExample(
                "add_enroll",
                value={"department_id": 1, "course_code": "CS201",
                       "faculty_user_id": 2001, "student_user_id": 1001},
                request_only=True,
            )
        ],
    )
    def post(self, request):
        ser = s.CourseEnrollmentCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        obj = profile_svc.add_course_enrollment(actor=request.principal, **ser.validated_data)
        return Response(
            s.CourseEnrollmentReadSerializer(obj).data, status=status.HTTP_201_CREATED
        )


# -- Role Assignments ---------------------------------------------------------
class RoleAssignmentListCreateView(APIView):
    throttle_scope = "dept_role_assign"

    def get_permissions(self):
        perm = (
            "department.role_assignment.assign"
            if self.request.method == "POST"
            else "department.role_assignment.view"
        )
        return [HasModuleGrant("department")(), HasPermission(perm)()]

    @extend_schema(
        summary="List time-bound department HOD and Dept_Admin role assignments",
        tags=["department"],
        responses=s.RoleAssignmentReadSerializer(many=True),
        examples=[OpenApiExample("roles", value={"results": []}, response_only=True)],
    )
    def get(self, request):
        qs = scoping.role_assignments_for(request.principal)
        dept_id = _int_param(request, "department")
        if dept_id is not None:
            qs = qs.filter(department_id=dept_id)
        return _paginate(request, qs, s.RoleAssignmentReadSerializer, self)

    @extend_schema(
        summary="Assign a time-bound HOD or Dept_Admin role (Institute Admin)",
        tags=["department"],
        request=s.RoleAssignmentCreateSerializer,
        responses={201: s.RoleAssignmentReadSerializer},
        examples=[
            OpenApiExample(
                "assign_role",
                value={
                    "department_id": 1,
                    "role_type": "hod",
                    "user_id": 2001,
                    "valid_from": "2026-08-01T00:00:00Z",
                    "valid_to": "2028-07-31T23:59:59Z",
                },
                request_only=True,
            )
        ],
    )
    def post(self, request):
        ser = s.RoleAssignmentCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        obj = role_svc.assign_role(actor=request.principal, **ser.validated_data)
        return Response(s.RoleAssignmentReadSerializer(obj).data, status=status.HTTP_201_CREATED)
