from django.db import models
from django.db.models import Q

from core.db.mixins import TimeStampedModel
from modules.department.models.department import Department


class InventoryItem(TimeStampedModel):
    department = models.ForeignKey(
        Department, on_delete=models.CASCADE, related_name="inventory_items"
    )
    sku = models.CharField(max_length=64)
    name = models.CharField(max_length=160)
    category = models.CharField(max_length=80, blank=True)
    unit = models.CharField(max_length=32, default="units")
    current_quantity = models.IntegerField(default=0)
    location = models.CharField(max_length=160, blank=True)
    description = models.TextField(blank=True)
    created_by_user_id = models.IntegerField()

    class Meta:
        ordering = ["name", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["department", "sku"],
                name="dept_inventory_unique_sku",
            ),
            models.CheckConstraint(
                condition=Q(current_quantity__gte=0),
                name="dept_inventory_qty_non_negative",
            ),
        ]
        indexes = [
            models.Index(fields=["department", "name"], name="dept_inv_dept_name_idx"),
        ]


class StockRequest(TimeStampedModel):
    STATUS_CHOICES = [
        ("pending_hod_approval", "Pending HOD Approval"),
        ("approved_for_issuance", "Approved for Issuance"),
        ("rejected", "Rejected"),
        ("issued", "Issued"),
    ]

    department = models.ForeignKey(
        Department, on_delete=models.CASCADE, related_name="stock_requests"
    )
    item = models.ForeignKey(
        InventoryItem, on_delete=models.PROTECT, related_name="stock_requests"
    )
    requester_user_id = models.IntegerField()
    requested_quantity = models.IntegerField()
    purpose = models.CharField(max_length=300, blank=True)
    status = models.CharField(
        max_length=32, choices=STATUS_CHOICES, default="pending_hod_approval"
    )
    hod_decided_by_user_id = models.IntegerField(null=True, blank=True)
    hod_decided_at = models.DateTimeField(null=True, blank=True)
    hod_note = models.CharField(max_length=300, blank=True)
    issued_by_user_id = models.IntegerField(null=True, blank=True)
    issued_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-id"]
        constraints = [
            models.CheckConstraint(
                condition=Q(requested_quantity__gt=0),
                name="dept_stock_req_qty_positive",
            ),
            models.CheckConstraint(
                condition=Q(
                    status__in=[
                        "pending_hod_approval",
                        "approved_for_issuance",
                        "rejected",
                        "issued",
                    ]
                ),
                name="dept_stock_req_status_valid",
            ),
        ]
        indexes = [
            models.Index(
                fields=["department", "status", "-id"],
                name="dept_stock_req_dept_st_idx",
            ),
            models.Index(
                fields=["requester_user_id", "-id"],
                name="dept_stock_req_user_idx",
            ),
        ]


class StockMovement(models.Model):
    # BR-DEPT-016: append-only immutable stock movement ledger.
    TYPE_CHOICES = [
        ("insertion", "Insertion"),
        ("issuance", "Issuance"),
    ]

    department = models.ForeignKey(
        Department, on_delete=models.CASCADE, related_name="stock_movements"
    )
    item = models.ForeignKey(
        InventoryItem, on_delete=models.PROTECT, related_name="movements"
    )
    stock_request = models.ForeignKey(
        StockRequest,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="movements",
    )
    movement_type = models.CharField(max_length=16, choices=TYPE_CHOICES)
    quantity_delta = models.IntegerField()
    balance_after = models.IntegerField()
    actor_user_id = models.IntegerField()
    note = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-id"]
        constraints = [
            models.CheckConstraint(
                condition=Q(movement_type__in=["insertion", "issuance"]),
                name="dept_stock_mov_type_valid",
            ),
            models.CheckConstraint(
                condition=Q(balance_after__gte=0),
                name="dept_stock_mov_bal_non_neg",
            ),
        ]
        indexes = [
            models.Index(
                fields=["department", "movement_type", "-id"],
                name="dept_stock_mov_dept_type_idx",
            ),
            models.Index(fields=["item", "-id"], name="dept_stock_mov_item_idx"),
        ]

    def __str__(self) -> str:
        return f"StockMovement({self.movement_type} {self.quantity_delta} item={self.item_id})"
