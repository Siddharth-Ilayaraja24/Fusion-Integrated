from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from core.api.exceptions import BadRequestError, ConflictError, NotFoundError, PermissionDeniedError
from modules.department.domain import errors as domain_errors
from modules.department.domain import rules
from modules.department.domain import state_machine as sm
from modules.department.models import InventoryItem, StockMovement, StockRequest
from modules.department.selectors.scoping import actor_lane, inventory_for, stock_requests_for
from modules.department.services import notifications
from modules.department.services.authz import require, require_department


@transaction.atomic
def insert_stock(
    *,
    department_id: int,
    actor,
    sku: str,
    name: str,
    quantity: int,
    category: str = "",
    unit: str = "units",
    location: str = "",
    description: str = "",
    note: str = "",
) -> InventoryItem:
    # UC-DEPT-019 / BR-DEPT-016 / AFR-DEPT-007 / AFR-DEPT-008 / AFR-DEPT-014.
    require(actor, "department.inventory.create")
    dept = require_department(actor, department_id)
    if quantity <= 0:
        raise BadRequestError("Inserted stock quantity must be positive.", code="invalid_quantity")
    clean_sku = (sku or "").strip().upper()
    clean_name = (name or "").strip()
    if not clean_sku or not clean_name:
        raise BadRequestError("SKU and item name are required.", code="missing_item_fields")

    item = (
        InventoryItem.objects.select_for_update()
        .filter(department=dept, sku=clean_sku)
        .first()
    )
    if item is None:
        item = InventoryItem.objects.create(
            department=dept,
            sku=clean_sku,
            name=clean_name,
            category=category.strip(),
            unit=(unit or "units").strip(),
            current_quantity=quantity,
            location=location.strip(),
            description=description.strip(),
            created_by_user_id=actor.user_id,
        )
    else:
        item.current_quantity += quantity
        item.name = clean_name
        if category:
            item.category = category.strip()
        if location:
            item.location = location.strip()
        if description:
            item.description = description.strip()
        item.save(
            update_fields=[
                "current_quantity",
                "name",
                "category",
                "location",
                "description",
                "updated_at",
            ]
        )

    StockMovement.objects.create(
        department=dept,
        item=item,
        stock_request=None,
        movement_type="insertion",
        quantity_delta=quantity,
        balance_after=item.current_quantity,
        actor_user_id=actor.user_id,
        note=(note or f"Stock insertion for {item.sku}")[:300],
    )
    return item


@transaction.atomic
def request_stock(
    *,
    item_id: int,
    actor,
    requested_quantity: int,
    purpose: str = "",
) -> StockRequest:
    # UC-DEPT-004 / BR-DEPT-005 / BR-DEPT-015 / AFR-DEPT-009 / AFR-DEPT-010 / AFR-DEPT-041..042.
    require(actor, "department.stock_request.create")
    item = (
        inventory_for(actor)
        .select_for_update()
        .select_related("department")
        .filter(pk=item_id)
        .first()
    )
    if item is None:
        raise NotFoundError("Inventory item not found.", code="inventory_item_not_found")

    try:
        rules.validate_stock_request(
            requested_quantity=requested_quantity,
            current_quantity=item.current_quantity,
        )
    except domain_errors.InsufficientStock as exc:
        raise ConflictError(exc.message, code=exc.code) from exc
    except domain_errors.ValidationRuleError as exc:
        raise BadRequestError(exc.message, code=exc.code) from exc

    req = StockRequest.objects.create(
        department=item.department,
        item=item,
        requester_user_id=actor.user_id,
        requested_quantity=requested_quantity,
        purpose=purpose.strip()[:300],
        status=sm.STOCK_PENDING,
    )

    # AFR-DEPT-041: notify Dept_Admin of new stock request.
    notifications.enqueue(
        department=item.department,
        topic="stock_request.submitted",
        dedupe_key=f"dept.stock.submitted.admin:{req.pk}",
        recipient_user_id=item.department.active_dept_admin_user_id,
        subject=f"[{item.department.code}] New stock request #{req.pk}",
        body=f"Faculty requested {requested_quantity} {item.unit} of {item.name}.",
        payload={"stock_request_id": req.pk, "item_id": item.pk},
    )
    # AFR-DEPT-042: notify HOD that authorization is required.
    notifications.enqueue(
        department=item.department,
        topic="stock_request.awaiting_hod",
        dedupe_key=f"dept.stock.submitted.hod:{req.pk}",
        recipient_user_id=item.department.active_hod_user_id,
        subject=f"[{item.department.code}] Stock request #{req.pk} requires HOD approval",
        body=(
            f"Please review request #{req.pk} for {requested_quantity} "
            f"{item.unit} of {item.name}."
        ),
        payload={"stock_request_id": req.pk, "item_id": item.pk},
    )
    return req


@transaction.atomic
def decide_stock_request(
    *,
    request_id: int,
    actor,
    approve: bool,
    note: str = "",
) -> StockRequest:
    # UC-DEPT-005 / BR-DEPT-006 / BW-DEPT-01 / BW-DEPT-02 / CW-DEPT-01 / AFR-DEPT-011 / 043.
    require(actor, "department.stock_request.approve")
    req = (
        stock_requests_for(actor)
        .select_for_update()
        .select_related("department", "item")
        .filter(pk=request_id)
        .first()
    )
    if req is None:
        raise NotFoundError("Stock request not found.", code="stock_request_not_found")
    if req.requester_user_id == actor.user_id:
        raise ConflictError(
            "You cannot approve or reject your own stock request.",
            code="self_approval_forbidden",
        )

    target = sm.STOCK_APPROVED if approve else sm.STOCK_REJECTED
    try:
        sm.resolve("stock_request", req.status, target, actor_lane(actor))
    except domain_errors.ActorNotAllowed as exc:
        raise PermissionDeniedError(exc.message, code=exc.code) from exc
    except domain_errors.InvalidTransition as exc:
        raise ConflictError(exc.message, code=exc.code) from exc

    req.status = target
    req.hod_decided_by_user_id = actor.user_id
    req.hod_decided_at = timezone.now()
    req.hod_note = note.strip()[:300]
    req.save(
        update_fields=[
            "status",
            "hod_decided_by_user_id",
            "hod_decided_at",
            "hod_note",
            "updated_at",
        ]
    )

    # AFR-DEPT-043: notify Faculty only on final Rejected outcome (not intermediate approval).
    if not approve:
        notifications.enqueue(
            department=req.department,
            topic="stock_request.rejected",
            dedupe_key=f"dept.stock.rejected:{req.pk}",
            recipient_user_id=req.requester_user_id,
            subject=f"[{req.department.code}] Stock request #{req.pk} rejected",
            body=f"Your request for {req.requested_quantity} {req.item.unit} of "
            f"{req.item.name} was rejected.",
            payload={"stock_request_id": req.pk, "outcome": "rejected"},
        )
    return req


@transaction.atomic
def issue_stock(*, request_id: int, actor, note: str = "") -> StockRequest:
    # UC-DEPT-006 / BR-DEPT-007 / BR-DEPT-016 / BW-DEPT-01 / CW-DEPT-01 / AFR-DEPT-012..015, 043.
    require(actor, "department.stock_request.update")
    req = (
        stock_requests_for(actor)
        .select_for_update()
        .select_related("department")
        .filter(pk=request_id)
        .first()
    )
    if req is None:
        raise NotFoundError("Stock request not found.", code="stock_request_not_found")

    try:
        sm.resolve("stock_request", req.status, sm.STOCK_ISSUED, actor_lane(actor))
    except domain_errors.ActorNotAllowed as exc:
        raise PermissionDeniedError(exc.message, code=exc.code) from exc
    except domain_errors.InvalidTransition as exc:
        raise ConflictError(exc.message, code=exc.code) from exc

    # Lock inventory item inside the same transaction so concurrent issues cannot go negative.
    item = InventoryItem.objects.select_for_update().get(pk=req.item_id)
    try:
        new_qty = rules.validate_stock_issuance(
            requested_quantity=req.requested_quantity,
            current_quantity=item.current_quantity,
        )
    except domain_errors.InsufficientStock as exc:
        raise ConflictError(exc.message, code=exc.code) from exc

    item.current_quantity = new_qty
    item.save(update_fields=["current_quantity", "updated_at"])

    req.status = sm.STOCK_ISSUED
    req.issued_by_user_id = actor.user_id
    req.issued_at = timezone.now()
    req.save(update_fields=["status", "issued_by_user_id", "issued_at", "updated_at"])

    StockMovement.objects.create(
        department=req.department,
        item=item,
        stock_request=req,
        movement_type="issuance",
        quantity_delta=-req.requested_quantity,
        balance_after=new_qty,
        actor_user_id=actor.user_id,
        note=(note or f"Issued for stock request #{req.pk}")[:300],
    )

    # AFR-DEPT-043: notify requesting Faculty of final Issued outcome.
    notifications.enqueue(
        department=req.department,
        topic="stock_request.issued",
        dedupe_key=f"dept.stock.issued:{req.pk}",
        recipient_user_id=req.requester_user_id,
        subject=f"[{req.department.code}] Stock request #{req.pk} issued",
        body=f"{req.requested_quantity} {item.unit} of {item.name} has been issued.",
        payload={"stock_request_id": req.pk, "outcome": "issued"},
    )
    return req
