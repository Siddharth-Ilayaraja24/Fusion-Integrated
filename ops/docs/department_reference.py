from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "10-department" / "department-reference.md"

LINKS: tuple[tuple[str, str, str], ...] = (
    ("BR-DEPT-001", "modules/department/services/announcements.py", "def create_announcement"),
    ("BR-DEPT-002", "modules/department/domain/rules.py", "def announcement_matches_viewer"),
    ("BR-DEPT-003", "modules/department/domain/rules.py", "def validate_announcement_payload"),
    ("BR-DEPT-004", "modules/department/services/announcements.py", "def update_announcement"),
    ("BR-DEPT-005", "modules/department/services/inventory.py", "def request_stock"),
    ("BR-DEPT-006", "modules/department/services/inventory.py", "def decide_stock_request"),
    ("BR-DEPT-007", "modules/department/services/inventory.py", "def issue_stock"),
    ("BR-DEPT-008", "modules/department/services/feedback.py", "def submit_feedback"),
    ("BR-DEPT-009", "modules/department/services/feedback.py", "def dispose_feedback"),
    ("BR-DEPT-010", "modules/department/domain/rules.py", "def detect_timetable_conflicts"),
    ("BR-DEPT-011", "modules/department/services/department.py", "def propose_official_change"),
    ("BR-DEPT-012", "modules/department/selectors/scoping.py", "def lab_resources_for"),
    ("BR-DEPT-013", "modules/department/services/department.py", "def decide_official_change"),
    ("BR-DEPT-015", "modules/department/domain/rules.py", "def validate_stock_request"),
    ("BR-DEPT-016", "modules/department/models/inventory.py", "class StockMovement"),
    ("BR-DEPT-017", "modules/department/selectors/scoping.py", "def feedback_for"),
    ("BR-DEPT-018", "modules/department/services/feedback.py", "def review_feedback"),
    ("BR-DEPT-019", "modules/department/domain/rules.py", "def project_profile_fields"),
    ("BR-DEPT-021", "modules/department/services/roles.py", "def assign_role"),
    ("BR-DEPT-022", "modules/department/models/roles.py", "dept_one_active_role_per_type"),
    ("BR-DEPT-023", "modules/department/domain/rules.py", "def validate_role_tenure"),
    ("BR-DEPT-024", "modules/department/services/roles.py", "def apply_effective_transitions"),
    ("UC-DEPT-001", "modules/department/api/views.py", "class AnnouncementListCreateView"),
    ("UC-DEPT-002", "modules/department/services/announcements.py", "def create_announcement"),
    ("UC-DEPT-003", "modules/department/api/views.py", "class AnnouncementDetailView"),
    ("UC-DEPT-004", "modules/department/services/inventory.py", "def request_stock"),
    ("UC-DEPT-005", "modules/department/services/inventory.py", "def decide_stock_request"),
    ("UC-DEPT-006", "modules/department/services/inventory.py", "def issue_stock"),
    ("UC-DEPT-007", "modules/department/services/feedback.py", "def submit_feedback"),
    ("UC-DEPT-008", "modules/department/services/feedback.py", "def review_feedback"),
    ("UC-DEPT-009", "modules/department/services/resources.py", "def create_timetable_slot"),
    ("UC-DEPT-010", "modules/department/services/department.py", "def update_general_details"),
    ("UC-DEPT-011", "modules/department/selectors/scoping.py", "def stock_movements_for"),
    ("UC-DEPT-012", "modules/department/services/department.py", "def decide_official_change"),
    ("UC-DEPT-014", "modules/department/services/feedback.py", "def dispose_feedback"),
    ("UC-DEPT-015", "modules/department/selectors/profiles.py", "def list_visible_profiles"),
    ("UC-DEPT-016", "modules/department/services/profiles.py", "def upsert_profile"),
    ("UC-DEPT-017", "modules/department/services/resources.py", "def create_or_update_lab"),
    ("UC-DEPT-018", "modules/department/selectors/scoping.py", "def programs_for"),
    ("UC-DEPT-019", "modules/department/services/inventory.py", "def insert_stock"),
    ("UC-DEPT-020", "modules/department/services/roles.py", "def assign_role"),
    ("UC-DEPT-022", "modules/department/services/roles.py", "def apply_effective_transitions"),
    ("BW-DEPT-01", "modules/department/domain/state_machine.py", "STOCK_TRANSITIONS"),
    ("BW-DEPT-02", "modules/department/domain/state_machine.py", "STOCK_TRANSITIONS"),
    ("CW-DEPT-01", "modules/department/domain/state_machine.py", "STOCK_TRANSITIONS"),
    ("BW-DEPT-03", "modules/department/domain/state_machine.py", "FEEDBACK_TRANSITIONS"),
    ("BW-DEPT-04", "modules/department/domain/state_machine.py", "FEEDBACK_TRANSITIONS"),
    ("CW-DEPT-02", "modules/department/domain/state_machine.py", "FEEDBACK_TRANSITIONS"),
    ("BW-DEPT-05", "modules/department/domain/state_machine.py", "OFFICIAL_CHANGE_TRANSITIONS"),
    ("BW-DEPT-06", "modules/department/domain/state_machine.py", "OFFICIAL_CHANGE_TRANSITIONS"),
    ("CW-DEPT-03", "modules/department/domain/state_machine.py", "OFFICIAL_CHANGE_TRANSITIONS"),
    ("BW-DEPT-07", "modules/department/domain/state_machine.py", "ROLE_ASSIGNMENT_TRANSITIONS"),
    ("BW-DEPT-08", "modules/department/domain/state_machine.py", "ROLE_ASSIGNMENT_TRANSITIONS"),
    ("CW-DEPT-04", "modules/department/domain/state_machine.py", "ROLE_ASSIGNMENT_TRANSITIONS"),
    ("CFR-DEPT-001", "modules/department/services/announcements.py", "def create_announcement"),
    ("CFR-DEPT-002", "modules/department/selectors/scoping.py", "def announcements_for"),
    ("CFR-DEPT-003", "modules/department/services/announcements.py", "def update_announcement"),
    ("CFR-DEPT-004", "modules/department/services/inventory.py", "def insert_stock"),
    ("CFR-DEPT-005", "modules/department/services/inventory.py", "def issue_stock"),
    ("CFR-DEPT-006", "modules/department/selectors/scoping.py", "def stock_movements_for"),
    ("CFR-DEPT-007", "modules/department/services/feedback.py", "def submit_feedback"),
    ("CFR-DEPT-008", "modules/department/services/feedback.py", "def dispose_feedback"),
    ("CFR-DEPT-009", "modules/department/services/profiles.py", "def upsert_profile"),
    ("CFR-DEPT-010", "modules/department/selectors/profiles.py", "def get_visible_profile"),
    ("CFR-DEPT-011", "modules/department/services/resources.py", "def create_timetable_slot"),
    ("CFR-DEPT-012", "modules/department/services/resources.py", "def create_or_update_lab"),
    ("CFR-DEPT-013", "modules/department/selectors/scoping.py", "def programs_for"),
    ("CFR-DEPT-014", "modules/department/services/department.py", "def update_general_details"),
    ("CFR-DEPT-015", "modules/department/services/department.py", "def decide_official_change"),
    ("CFR-DEPT-016", "modules/department/services/roles.py", "def apply_effective_transitions"),
)


def find_line(rel_path: str, needle: str) -> int:
    target = ROOT / rel_path
    if not target.exists():
        raise FileNotFoundError(f"Missing target file: {rel_path}")
    for idx, line in enumerate(target.read_text().splitlines(), start=1):
        if needle in line:
            return idx
    raise ValueError(f"Needle {needle!r} not found in {rel_path}")


def main() -> int:
    rows = [
        "# Department Module — Specification-to-Code Reference",
        "",
        "Generated by `ops/docs/department_reference.py`. Every link resolves to a live symbol.",
        "",
        "| Spec ID | Enforcement Point |",
        "|---|---|",
    ]
    for spec_id, rel_path, needle in LINKS:
        lineno = find_line(rel_path, needle)
        rows.append(f"| `{spec_id}` | `{rel_path}:{lineno}` (`{needle}`) |")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(rows) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)} ({len(LINKS)} verified links)")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileNotFoundError, ValueError) as exc:
        print(f"department_reference failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
