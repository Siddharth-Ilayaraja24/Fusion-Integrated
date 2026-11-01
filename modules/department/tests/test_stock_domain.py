import pytest
from modules.department.domain.stock import next_state, IllegalTransition, TRANSITIONS

@pytest.mark.parametrize("state, event, role_kind, expected_next_state", TRANSITIONS.items(), ids=lambda x: f"{x[0]}_{x[1]}_{x[2]}")
def test_next_state_valid_transitions(state, event, role_kind, expected_next_state):
    """
    Tests that next_state returns the correct next state for defined transitions.
    """
    assert next_state(state, event, role_kind) == expected_next_state

@pytest.mark.parametrize("state, event, role_kind", [
    ("pending_hod_approval", "approve", "dept_admin"),
    ("pending_hod_approval", "reject", "dept_admin"),
    ("pending_hod_approval", "issue", "hod"),
    ("approved_for_issuance", "approve", "faculty"),
    ("approved_for_issuance", "reject", "hod"),
    ("approved_for_issuance", "issue", "hod"),
    ("rejected", "approve", "hod"),
    ("rejected", "reject", "dept_admin"),
    ("rejected", "issue", "dept_admin"),
    ("issued", "approve", "faculty"),
    ("issued", "reject", "hod"),
    ("issued", "issue", "dept_admin"),
])
def test_next_state_illegal_transitions(state, event, role_kind):
    """
    Tests that next_state raises IllegalTransition for combinations not in TRANSITIONS.
    """
    with pytest.raises(IllegalTransition) as excinfo:
        next_state(state, event, role_kind)
    assert f"Invalid transition: {state} with event {event} by role {role_kind}" in str(excinfo.value)
