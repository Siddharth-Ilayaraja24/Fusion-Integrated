from __future__ import annotations

from core.api.exceptions import NotFoundError, PermissionDeniedError
from modules.department.models import Department
from modules.department.selectors.scoping import departments_for


def require(actor, *codes: str) -> None:
    check = getattr(actor, "has_permission", None)
    if not (check and any(check(c) for c in codes)):
        raise PermissionDeniedError(
            "You do not have permission to perform this department action.",
            code="permission_denied",
        )


def require_department(actor, department_id: int) -> Department:
    # Scope check on every write: an out-of-scope department_id returns 404, never 403.
    dept = departments_for(actor).filter(pk=department_id).first()
    if dept is None:
        raise NotFoundError("Department not found.", code="department_not_found")
    return dept
