from __future__ import annotations


class DepartmentRuleError(Exception):
    def __init__(self, message: str, *, code: str = "department_rule_error"):
        super().__init__(message)
        self.message = message
        self.code = code


class InvalidTransition(DepartmentRuleError):
    def __init__(self, entity: str, frm: str, to: str):
        super().__init__(
            f"Cannot move {entity} from {frm!r} to {to!r}.",
            code="invalid_transition",
        )
        self.entity, self.frm, self.to = entity, frm, to


class ActorNotAllowed(DepartmentRuleError):
    def __init__(self, actor_kind: str, entity: str, frm: str, to: str):
        super().__init__(
            f"A {actor_kind} may not move {entity} from {frm!r} to {to!r}.",
            code="actor_not_allowed",
        )
        self.actor_kind, self.entity, self.frm, self.to = actor_kind, entity, frm, to


class ValidationRuleError(DepartmentRuleError):
    def __init__(self, message: str, *, code: str = "validation_failed"):
        super().__init__(message, code=code)


class InsufficientStock(DepartmentRuleError):
    def __init__(self, requested: int, available: int):
        super().__init__(
            f"Requested quantity ({requested}) exceeds available inventory ({available}).",
            code="insufficient_stock",
        )
        self.requested, self.available = requested, available


class TimetableConflict(DepartmentRuleError):
    def __init__(self, reason: str):
        super().__init__(reason, code="timetable_conflict")


class ForbiddenOfficialField(DepartmentRuleError):
    def __init__(self, field_name: str):
        super().__init__(
            f"Field {field_name!r} cannot be edited through the official-change workflow.",
            code="forbidden_official_field",
        )


class InvalidTenure(DepartmentRuleError):
    def __init__(self, message: str):
        super().__init__(message, code="invalid_tenure")


class SelfApprovalForbidden(DepartmentRuleError):
    def __init__(self, message: str):
        super().__init__(message, code="self_approval_forbidden")
