from __future__ import annotations

from dataclasses import dataclass

from modules.department.domain.errors import ActorNotAllowed, InvalidTransition

# Actor lane constants shared across all department state machines.
ACTOR_STUDENT = "student"
ACTOR_FACULTY = "faculty"
ACTOR_DEPT_ADMIN = "dept_admin"
ACTOR_HOD = "hod"
ACTOR_INSTITUTE_ADMIN = "institute_admin"
ACTOR_SYSTEM = "system"


@dataclass(frozen=True)
class Transition:
    frm: str
    to: str
    permission: str
    actors: frozenset[str]


# CW-DEPT-01 / BW-DEPT-01 / BW-DEPT-02: stock request lifecycle.
STOCK_PENDING = "pending_hod_approval"
STOCK_APPROVED = "approved_for_issuance"
STOCK_REJECTED = "rejected"
STOCK_ISSUED = "issued"
STOCK_TERMINAL = frozenset({STOCK_REJECTED, STOCK_ISSUED})

STOCK_TRANSITIONS: tuple[Transition, ...] = (
    Transition(
        STOCK_PENDING, STOCK_APPROVED, "department.stock_request.approve", frozenset({ACTOR_HOD})
    ),
    Transition(
        STOCK_PENDING, STOCK_REJECTED, "department.stock_request.approve", frozenset({ACTOR_HOD})
    ),
    Transition(
        STOCK_APPROVED, STOCK_ISSUED, "department.stock_request.update",
        frozenset({ACTOR_DEPT_ADMIN}),
    ),
)

# CW-DEPT-02 / BW-DEPT-03 / BW-DEPT-04: confidential feedback lifecycle.
FEEDBACK_NEW = "new"
FEEDBACK_UNDER_REVIEW = "under_review"
FEEDBACK_RESOLVED = "resolved"
FEEDBACK_CLOSED = "closed"
FEEDBACK_TERMINAL = frozenset({FEEDBACK_RESOLVED, FEEDBACK_CLOSED})

FEEDBACK_TRANSITIONS: tuple[Transition, ...] = (
    Transition(
        FEEDBACK_NEW, FEEDBACK_UNDER_REVIEW, "department.feedback.review",
        frozenset({ACTOR_DEPT_ADMIN}),
    ),
    # AFR-DEPT-021: Dept_Admin may close a simple issue during initial review.
    Transition(
        FEEDBACK_NEW, FEEDBACK_CLOSED, "department.feedback.review",
        frozenset({ACTOR_DEPT_ADMIN}),
    ),
    Transition(
        FEEDBACK_UNDER_REVIEW, FEEDBACK_RESOLVED, "department.feedback.update",
        frozenset({ACTOR_DEPT_ADMIN, ACTOR_HOD}),
    ),
    Transition(
        FEEDBACK_UNDER_REVIEW, FEEDBACK_CLOSED, "department.feedback.update",
        frozenset({ACTOR_DEPT_ADMIN, ACTOR_HOD}),
    ),
)

# CW-DEPT-03 / BW-DEPT-05 / BW-DEPT-06: official department detail change lifecycle.
OFFICIAL_PENDING = "pending_hod_approval"
OFFICIAL_APPROVED = "approved"
OFFICIAL_REJECTED = "rejected"
OFFICIAL_TERMINAL = frozenset({OFFICIAL_APPROVED, OFFICIAL_REJECTED})

OFFICIAL_CHANGE_TRANSITIONS: tuple[Transition, ...] = (
    Transition(
        OFFICIAL_PENDING, OFFICIAL_APPROVED, "department.official_change.approve",
        frozenset({ACTOR_HOD}),
    ),
    Transition(
        OFFICIAL_PENDING, OFFICIAL_REJECTED, "department.official_change.approve",
        frozenset({ACTOR_HOD}),
    ),
)

# CW-DEPT-04 / BW-DEPT-07 / BW-DEPT-08: department role assignment lifecycle.
ROLE_SCHEDULED = "scheduled"
ROLE_ACTIVE = "active"
ROLE_SUPERSEDED = "superseded"
ROLE_EXPIRED = "expired"
ROLE_CANCELLED = "cancelled"
ROLE_TERMINAL = frozenset({ROLE_SUPERSEDED, ROLE_EXPIRED, ROLE_CANCELLED})

ROLE_ASSIGNMENT_TRANSITIONS: tuple[Transition, ...] = (
    Transition(
        ROLE_SCHEDULED, ROLE_ACTIVE, "department.role_assignment.revoke",
        frozenset({ACTOR_SYSTEM}),
    ),
    Transition(
        ROLE_SCHEDULED, ROLE_CANCELLED, "department.role_assignment.assign",
        frozenset({ACTOR_INSTITUTE_ADMIN}),
    ),
    Transition(
        ROLE_ACTIVE, ROLE_SUPERSEDED, "department.role_assignment.revoke",
        frozenset({ACTOR_SYSTEM}),
    ),
    Transition(
        ROLE_ACTIVE, ROLE_EXPIRED, "department.role_assignment.revoke",
        frozenset({ACTOR_SYSTEM}),
    ),
)

_TABLES: dict[str, tuple[Transition, ...]] = {
    "stock_request": STOCK_TRANSITIONS,
    "feedback": FEEDBACK_TRANSITIONS,
    "official_change": OFFICIAL_CHANGE_TRANSITIONS,
    "role_assignment": ROLE_ASSIGNMENT_TRANSITIONS,
}


def resolve(entity: str, frm: str, to: str, actor_kind: str | None = None) -> Transition:
    table = _TABLES[entity]
    match = next((t for t in table if t.frm == frm and t.to == to), None)
    if match is None:
        raise InvalidTransition(entity, frm, to)
    if actor_kind is not None and actor_kind not in match.actors:
        raise ActorNotAllowed(actor_kind, entity, frm, to)
    return match


def is_legal(entity: str, frm: str, to: str) -> bool:
    return any(t.frm == frm and t.to == to for t in _TABLES[entity])


def allowed_targets(entity: str, frm: str, actor_kind: str | None = None) -> list[str]:
    return sorted(
        t.to
        for t in _TABLES[entity]
        if t.frm == frm and (actor_kind is None or actor_kind in t.actors)
    )
