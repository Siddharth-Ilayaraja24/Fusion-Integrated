# Department Module Blueprint

## Step 3.1 (a) — Traceability table

Every live Business Rule (`BR-DEPT-*`), Use Case (`UC-DEPT-*`), Workflow (`BW-DEPT-*`, `CW-DEPT-*`), Coherent Requirement (`CFR-DEPT-*`), and Atomic Requirement (`AFR-DEPT-*` / historical `FR-DEPT-*`) from `6-DEPT` v1.2 is mapped below. Retired IDs (`BR-DEPT-014`, `UC-DEPT-013`, `UC-DEPT-021`, `FR-DEPT-032`, `FR-DEPT-033`) are excluded.

| Id | What it requires | Layer it belongs in | Enforcement point (planned) | Notes |
|---|---|---|---|---|
| `BR-DEPT-001` | Only Faculty, Dept_Admin, or HOD may create and publish announcements | `api/` + `services/` | `HasPermission("department.announcement.create")` + `services/announcements.py::create_announcement` | Closed RBAC verb `create` |
| `BR-DEPT-002` | Filter announcement visibility by viewer role, program, and academic year | `domain/` + `selectors/` | `domain/rules.py::announcement_matches_viewer` + `selectors/scoping.py::announcements_for` | Out-of-scope returns 404 |
| `BR-DEPT-003` | Announcement requires non-empty content and valid target-scope info | `domain/` + `services/` | `domain/rules.py::validate_announcement_payload` + `services/announcements.py::create_announcement` | Also enforced on HOD edit |
| `BR-DEPT-004` | Only HOD may edit, hide, or delete an active announcement | `api/` + `services/` | `HasPermission("department.announcement.update" / "delete")` + `services/announcements.py` | Non-HOD gets 403 |
| `BR-DEPT-005` | Only Faculty may submit stock requests | `api/` + `services/` | `HasPermission("department.stock_request.create")` + `services/inventory.py::request_stock` | Non-Faculty gets 403 |
| `BR-DEPT-006` | Only HOD may approve or reject a pending Faculty stock request | `domain/` + `services/` | `domain/state_machine.py` + `services/inventory.py::decide_stock_request` | Self-approval blocked |
| `BR-DEPT-007` | Dept_Admin may issue stock only when HOD-approved | `domain/` + `services/` | `domain/state_machine.py` + `services/inventory.py::issue_stock` | Transactional `select_for_update` |
| `BR-DEPT-008` | Only authenticated Students and Faculty may submit feedback | `api/` + `services/` | `HasPermission("department.feedback.create")` + `services/feedback.py::submit_feedback` | Non-eligible gets 403 |
| `BR-DEPT-009` | Only Dept_Admin or HOD may mark feedback Resolved or Closed | `domain/` + `services/` | `domain/state_machine.py` + `services/feedback.py::dispose_feedback` | Includes Dept_Admin simple-issue close |
| `BR-DEPT-010` | Block timetable save when overlapping slots are detected | `domain/` + `services/` | `domain/rules.py::detect_timetable_conflicts` + `services/resources.py::save_timetable_slot` | Checks room, faculty, and cohort overlap |
| `BR-DEPT-011` | Official department-detail changes remain pending until HOD approval | `domain/` + `services/` | `domain/rules.py::validate_official_change_field` + `services/department.py::propose_official_change` | Headship excluded (`AFR-DEPT-053`) |
| `BR-DEPT-012` | Faculty resource views limited to Faculty scope (labs + relevant issued stock) | `selectors/` | `selectors/scoping.py::lab_resources_for`, `issued_stock_history_for` | Queryset narrowing |
| `BR-DEPT-013` | Only HOD may approve or reject pending official department-detail changes | `domain/` + `services/` | `domain/state_machine.py` + `services/department.py::decide_official_change` | Self-approval blocked |
| `BR-DEPT-015` | Stock request enters HOD approval only when current inventory is sufficient | `domain/` + `services/` | `domain/rules.py::validate_stock_request` + `services/inventory.py::request_stock` | Issuance also guards non-negative stock |
| `BR-DEPT-016` | Every stock insertion and issuance appends an immutable movement log | `models/` + `services/` | `models/inventory.py::StockMovement` + `services/inventory.py::insert_stock`, `issue_stock` | Append-only ledger; no edit/delete API |
| `BR-DEPT-017` | Feedback accessible only to submitter and authorized Dept_Admin/HOD | `selectors/` | `selectors/scoping.py::feedback_for` | Foreign feedback returns 404 |
| `BR-DEPT-018` | New feedback must undergo Dept_Admin initial review before HOD oversight | `domain/` + `selectors/` + `services/` | `domain/state_machine.py` + `selectors/scoping.py::feedback_for` + `services/feedback.py` | HOD cannot view/dispose `new` feedback |
| `BR-DEPT-019` | Role- and relationship-specific profile visibility excluding sensitive data | `domain/` + `selectors/` | `domain/rules.py::project_profile_fields` + `selectors/profiles.py` | `sensitive_personal_data` always stripped |
| `BR-DEPT-021` | Only central authority assigns HOD/Dept_Admin; Headship derived from active HOD | `api/` + `services/` | `HasPermission("department.role_assignment.assign")` + `services/roles.py` | Syncs `Department.active_hod_user_id` |
| `BR-DEPT-022` | Exactly one active HOD and one active Dept_Admin per department | `models/` + `services/` | Partial `UniqueConstraint` `dept_one_active_role_per_type` + `services/roles.py::apply_effective_transitions` | Enforced under `select_for_update` + DB |
| `BR-DEPT-023` | Each HOD and Dept_Admin assignment is time-bounded | `domain/` + `models/` | `domain/rules.py::validate_role_tenure` + DB `CheckConstraint(valid_to > valid_from)` | Rejects open-ended or inverted tenure |
| `BR-DEPT-024` | Effective reassignment immediately revokes outgoing and grants incoming access | `services/` + `tasks.py` | `services/roles.py::apply_effective_transitions` + `tasks.py::apply_role_transitions` | Live IAM projection noted in Step 3.8 (h) |
| `UC-DEPT-001` | View Announcements | `selectors/` + `api/` | `GET /api/v1/department/announcements` | `CFR-DEPT-002`, `AFR-DEPT-002`, `AFR-DEPT-003` |
| `UC-DEPT-002` | Create Announcement | `services/` + `api/` | `POST /api/v1/department/announcements` | `CFR-DEPT-001`, `AFR-DEPT-001`, `AFR-DEPT-046` |
| `UC-DEPT-003` | Manage Active Announcement | `services/` + `api/` | `PATCH/DELETE /api/v1/department/announcements/{id}`, `POST .../hide` | `CFR-DEPT-003`, `AFR-DEPT-004..006` |
| `UC-DEPT-004` | Request Stock Item | `services/` + `api/` | `POST /api/v1/department/stock-requests` | `CFR-DEPT-005`, `AFR-DEPT-009`, `010`, `041`, `042` |
| `UC-DEPT-005` | Approve or Reject Stock Request | `services/` + `api/` | `POST /api/v1/department/stock-requests/{id}/decide` | `CFR-DEPT-005`, `AFR-DEPT-011`, `AFR-DEPT-043` |
| `UC-DEPT-006` | Allocate and Issue Stock | `services/` + `api/` | `POST /api/v1/department/stock-requests/{id}/issue` | `CFR-DEPT-004`, `005`, `AFR-DEPT-008`, `012`, `013`, `015`, `043` |
| `UC-DEPT-007` | Submit Feedback | `services/` + `api/` | `POST /api/v1/department/feedback` | `CFR-DEPT-007`, `AFR-DEPT-017`, `018`, `044` |
| `UC-DEPT-008` | Initial Review and Disposition of Feedback | `services/` + `api/` | `POST /api/v1/department/feedback/{id}/review`, `POST .../dispose` | `CFR-DEPT-007`, `008`, `AFR-DEPT-018..022`, `045` |
| `UC-DEPT-009` | Manage Timetable | `services/` + `api/` | `POST /api/v1/department/timetables`, `PATCH /api/v1/department/timetables/{id}` | `CFR-DEPT-011`, `AFR-DEPT-029..031` |
| `UC-DEPT-010` | Update Department Details | `services/` + `api/` | `PATCH /api/v1/department/departments/{id}`, `POST /api/v1/department/official-changes` | `CFR-DEPT-014`, `015`, `AFR-DEPT-038`, `039` |
| `UC-DEPT-011` | View Department Resources | `selectors/` + `api/` | `GET /api/v1/department/labs`, `GET /api/v1/department/stock-movements` | `CFR-DEPT-006`, `012`, `AFR-DEPT-016`, `035` |
| `UC-DEPT-012` | Approve Official Department Changes | `services/` + `api/` | `POST /api/v1/department/official-changes/{id}/decide` | `CFR-DEPT-015`, `AFR-DEPT-039`, `040` |
| `UC-DEPT-014` | HOD Oversight and Resolution of Feedback | `selectors/` + `services/` + `api/` | `GET /api/v1/department/feedback`, `POST /api/v1/department/feedback/{id}/dispose` | `CFR-DEPT-008`, `AFR-DEPT-018`, `022`, `023`, `045` |
| `UC-DEPT-015` | View Department User Profiles | `selectors/` + `api/` | `GET /api/v1/department/profiles`, `GET /api/v1/department/profiles/{id}` | `CFR-DEPT-010`, `AFR-DEPT-025..028` |
| `UC-DEPT-016` | Manage Department User Profiles | `services/` + `api/` | `POST /api/v1/department/profiles`, `PATCH /api/v1/department/profiles/{id}`, `POST /api/v1/department/roster` | `CFR-DEPT-009`, `AFR-DEPT-024` |
| `UC-DEPT-017` | Manage Lab Profiles | `services/` + `api/` | `POST /api/v1/department/labs`, `PATCH /api/v1/department/labs/{id}` | `CFR-DEPT-012`, `AFR-DEPT-034` |
| `UC-DEPT-018` | View Academic Program Information and Timetable | `selectors/` + `api/` | `GET /api/v1/department/programs`, `GET /api/v1/department/timetables` | `CFR-DEPT-013`, `AFR-DEPT-036`, `037` |
| `UC-DEPT-019` | Manage Inventory Records | `services/` + `api/` | `GET/POST /api/v1/department/inventory` | `CFR-DEPT-004`, `AFR-DEPT-007`, `008`, `014` |
| `UC-DEPT-020` | Maintain Department Role Assignments | `services/` + `api/` | `GET/POST /api/v1/department/role-assignments` | `CFR-DEPT-016`, `AFR-DEPT-047`, `048`, `051`, `052` |
| `UC-DEPT-022` | Apply Effective Department Role Transition | `services/` + `tasks.py` | `services/roles.py::apply_effective_transitions` + `tasks.py::apply_role_transitions` | `CFR-DEPT-016`, `AFR-DEPT-048..053` |
| `BW-DEPT-01`, `02`, `CW-DEPT-01` | Stock Request, Approval and Issuance Lifecycle | `domain/state_machine.py` + `services/inventory.py` | `STOCK_TRANSITIONS` + `request_stock` / `decide_stock_request` / `issue_stock` | `CFR-DEPT-005` |
| `BW-DEPT-03`, `04`, `CW-DEPT-02` | Feedback Handling Lifecycle | `domain/state_machine.py` + `services/feedback.py` | `FEEDBACK_TRANSITIONS` + `submit_feedback` / `review_feedback` / `dispose_feedback` | `CFR-DEPT-007`, `CFR-DEPT-008` |
| `BW-DEPT-05`, `06`, `CW-DEPT-03` | Official Department Change Lifecycle | `domain/state_machine.py` + `services/department.py` | `OFFICIAL_CHANGE_TRANSITIONS` + `propose_official_change` / `decide_official_change` | `CFR-DEPT-015` |
| `BW-DEPT-07`, `08`, `CW-DEPT-04` | Department Role Reassignment Lifecycle | `domain/state_machine.py` + `services/roles.py` | `ROLE_ASSIGNMENT_TRANSITIONS` + `assign_role` / `apply_effective_transitions` | `CFR-DEPT-016` |
| `CFR-DEPT-001..016`, `AFR-DEPT-001..031`, `034..053` | All 16 CFRs and 51 active AFRs (preserving historical `FR-DEPT-*` continuity) | `domain/` + `models/` + `selectors/` + `services/` + `api/` | Mapped 1:1 through the UCs, BRs, and WFs above | Verified by `ops/docs/department_reference.py` and test citations |

## Step 3.2 (b) — Domain model

All person references are plain integer `user_id` fields (`core/db/mixins.py::UserScopedModel` or explicit `IntegerField`); zero cross-module foreign keys. All indexes and constraints are explicitly named.

1. **`Department`** (`models/department.py`): `code` (unique slug, e.g. `CSE`), `name`, `description`, `contact_email`, `location`, `website_url`, `core_policies`, `active_hod_user_id` (nullable int, derived from active HOD assignment), `active_dept_admin_user_id` (nullable int).
2. **`OfficialDetailChange`** (`models/department.py`): FK `department`, `field_name` (`name` | `core_policies`), `proposed_value`, `previous_value`, `status` (`pending_hod_approval` | `approved` | `rejected`), `proposed_by_user_id`, `decided_by_user_id`, `decided_at`, `decision_note`. DB `CheckConstraint` restricting `field_name` to `("name", "core_policies")` and `status` to valid values.
3. **`DepartmentProgram`** (`models/department.py`): FK `department`, `code`, `name`, `degree_level`, `duration_years`, `description`, `is_active`. `UniqueConstraint(fields=["department", "code"])`.
4. **`Announcement`** (`models/announcements.py`): FK `department`, `title`, `content`, `target_roles` (JSON list), `target_programs` (JSON list), `target_academic_years` (JSON list), `status` (`active` | `hidden` | `deleted`), `created_by_user_id`, `updated_by_user_id`.
5. **`InventoryItem`** (`models/inventory.py`): FK `department`, `sku`, `name`, `category`, `unit`, `current_quantity` (`CheckConstraint(current_quantity >= 0)`), `location`, `description`, `created_by_user_id`. `UniqueConstraint(fields=["department", "sku"])`.
6. **`StockRequest`** (`models/inventory.py`): FK `department`, FK `item`, `requester_user_id`, `requested_quantity` (`CheckConstraint(requested_quantity > 0)`), `purpose`, `status`, `hod_decided_by_user_id`, `hod_decided_at`, `hod_note`, `issued_by_user_id`, `issued_at`.
7. **`StockMovement`** (`models/inventory.py`, append-only ledger): FK `department`, FK `item`, nullable FK `stock_request`, `movement_type` (`insertion` | `issuance`), `quantity_delta`, `balance_after` (`CheckConstraint(balance_after >= 0)`), `actor_user_id`, `note`, `created_at`.
8. **`Feedback`** (`models/feedback.py`): FK `department`, `submitter_user_id`, `submitter_role`, `subject`, `body`, `category`, `status`, `initial_reviewed_by_user_id`, `initial_reviewed_at`, `resolved_by_user_id`, `resolved_at`, `resolution_note`.
9. **`FeedbackTransition`** (`models/feedback.py`, append-only audit): FK `feedback`, `from_status`, `to_status`, `actor_user_id`, `actor_role`, `note`, `created_at`.
10. **`TimetableSlot`** (`models/resources.py`): FK `department`, `slot_kind` (`class` | `lab`), `program`, `academic_year`, `section`, `course_code`, `course_title`, `faculty_user_id`, `room`, `day_of_week` (`0..6`), `start_time`, `end_time`, `is_active`, `updated_by_user_id`. `CheckConstraint(end_time > start_time)` and `CheckConstraint(day_of_week >= 0, day_of_week <= 6)`.
11. **`LabResource`** (`models/resources.py`): FK `department`, `lab_code`, `name`, `location`, `equipment_summary`, `capacity` (`CheckConstraint(capacity >= 0)`), `status`, `incharge_user_id`, `updated_by_user_id`. `UniqueConstraint(fields=["department", "lab_code"])`.
12. **`DepartmentProfile`** (`models/profiles.py`): FK `department`, `user_id`, `profile_kind` (`student` | `faculty` | `alumni`), `display_name`, `email`, `program`, `academic_year`, `designation_title`, `office_room`, `research_area`, `graduation_year`, `current_affiliation`, `academic_notes`, `sensitive_personal_data` (JSON dict, never serialized). `UniqueConstraint(fields=["department", "user_id"])`.
13. **`CourseEnrollment`** (`models/profiles.py`): FK `department`, `course_code`, `faculty_user_id`, `student_user_id`, `academic_year`. `UniqueConstraint(fields=["department", "course_code", "faculty_user_id", "student_user_id"])`.
14. **`DepartmentRoleAssignment`** (`models/roles.py`): FK `department`, `role_type` (`hod` | `dept_admin`), `user_id`, `valid_from`, `valid_to`, `status` (`scheduled` | `active` | `superseded` | `expired` | `cancelled`), `assigned_by_user_id`, `activated_at`, `revoked_at`. `CheckConstraint(valid_to > valid_from)` and partial `UniqueConstraint(fields=["department", "role_type"], condition=Q(status="active"), name="dept_one_active_role_per_type")`.
15. **`DepartmentNotification`** (`models/notifications.py`): FK `department`, `topic`, `dedupe_key` (unique), `recipient_user_id`, `subject`, `body`, `payload`, `status`, `attempts`, `sent_at`, `last_error`.

## Step 3.3 (c) — State machine

Four declarative transition tables in `modules/department/domain/state_machine.py` (pure Python, zero Django imports). Every service write calls `resolve_transition(table, frm, to, actor_kind)` under `select_for_update()`.

- **Stock Request (`CW-DEPT-01`):**
  - `(pending_hod_approval, approved_for_issuance, hod)`
  - `(pending_hod_approval, rejected, hod)`
  - `(approved_for_issuance, issued, dept_admin)`
  - Terminal: `{rejected, issued}`.
- **Feedback (`CW-DEPT-02`):**
  - `(new, under_review, dept_admin)`
  - `(new, closed, dept_admin)` *(simple-issue close during initial review, `AFR-DEPT-021`)*
  - `(under_review, resolved, dept_admin | hod)`
  - `(under_review, closed, dept_admin | hod)`
  - Terminal: `{resolved, closed}`.
- **Official Department Detail Change (`CW-DEPT-03`):**
  - `(pending_hod_approval, approved, hod)`
  - `(pending_hod_approval, rejected, hod)`
  - Terminal: `{approved, rejected}`.
- **Department Role Assignment (`CW-DEPT-04`):**
  - `(scheduled, active, system)`
  - `(scheduled, cancelled, institute_admin)`
  - `(active, superseded, system)`
  - `(active, expired, system)`
  - Terminal: `{superseded, expired, cancelled}`.

## Step 3.4 (d) — Permission list

`MODULE = {"code": "department", "label": "Department", "icon": "Buildings", "base_path": "/department", "nav_section": "Department", "sort_order": 40, "status": "active"}`.

All permission codes follow `department.<singular_noun>.<verb>` using the closed verb vocabulary from `docs/02-iam/rbac-model.md`. No auth tables are created in `fusion_integrated`.

- `department.department.view`, `department.department.update`
- `department.official_change.view`, `department.official_change.approve`
- `department.announcement.view`, `department.announcement.create`, `department.announcement.update`, `department.announcement.delete`
- `department.inventory.view`, `department.inventory.create`
- `department.stock_request.view`, `department.stock_request.create`, `department.stock_request.approve`, `department.stock_request.update`
- `department.stock_movement.view`
- `department.feedback.view`, `department.feedback.create`, `department.feedback.review`, `department.feedback.update`
- `department.timetable.view`, `department.timetable.create`, `department.timetable.update`
- `department.lab.view`, `department.lab.update`
- `department.program.view`, `department.program.update`
- `department.profile.view`, `department.profile.update`, `department.roster.update`
- `department.role_assignment.view`, `department.role_assignment.assign`
- `SYSTEM_PERMISSIONS = ["department.role_assignment.revoke"]`

`ROLE_GRANTS` maps exact `globals_designation` names:
- `student`: `department.view`, `announcement.view`, `feedback.view`, `feedback.create`, `timetable.view`, `program.view`, `profile.view`
- `faculty`: `department.view`, `announcement.view`, `announcement.create`, `inventory.view`, `stock_request.view`, `stock_request.create`, `stock_movement.view`, `feedback.view`, `feedback.create`, `timetable.view`, `lab.view`, `program.view`, `profile.view`
- `acadadmin`: `department.view`, `role_assignment.view`, `role_assignment.assign`
- `HOD (CSE)`, `HOD (Design)`, `HOD (ECE)`, `HOD (Liberal Arts)`, `HOD (ME)`, `HOD (NS)`: `department.view`, `announcement.view`, `announcement.create`, `announcement.update`, `announcement.delete`, `inventory.view`, `stock_request.view`, `stock_request.approve`, `stock_movement.view`, `feedback.view`, `feedback.update`, `timetable.view`, `lab.view`, `program.view`, `profile.view`, `official_change.view`, `official_change.approve`
- `dept_admin`, `deptadmin_cse`, `deptadmin_design`, `deptadmin_ece`, `deptadmin_liberalarts`, `deptadmin_me`, `deptadmin_ns`, `deptadmin_sm`: `department.view`, `department.update`, `announcement.view`, `announcement.create`, `inventory.view`, `inventory.create`, `stock_request.view`, `stock_request.update`, `stock_movement.view`, `feedback.view`, `feedback.review`, `feedback.update`, `timetable.view`, `timetable.create`, `timetable.update`, `lab.view`, `lab.update`, `program.view`, `program.update`, `profile.view`, `profile.update`, `roster.update`, `official_change.view`

## Step 3.5 (e) — Endpoint list and client routes

All API paths sit under `/api/v1/department/` and enforce `HasModuleGrant("department")` plus `HasPermission(...)`.

| Method | Path | Permission Gate | Returns | Rule / UC IDs |
|---|---|---|---|---|
| `GET` | `/departments` | `department.department.view` | Paginated `Department` list | `UC-DEPT-010`, `AFR-DEPT-053` |
| `GET` / `PATCH` | `/departments/{id}` | `department.department.view` / `.update` | `Department` | `UC-DEPT-010`, `AFR-DEPT-038`, `AFR-DEPT-053` |
| `GET` / `POST` | `/official-changes` | `department.official_change.view` / `department.department.update` | `OfficialDetailChange` | `UC-DEPT-010`, `BR-DEPT-011`, `AFR-DEPT-039` |
| `POST` | `/official-changes/{id}/decide` | `department.official_change.approve` | `OfficialDetailChange` | `UC-DEPT-012`, `BR-DEPT-013`, `AFR-DEPT-040`, `CW-DEPT-03` |
| `GET` / `POST` | `/announcements` | `department.announcement.view` / `.create` | `Announcement` | `UC-DEPT-001`, `UC-DEPT-002`, `BR-DEPT-001..003`, `AFR-DEPT-046` |
| `GET` / `PATCH` / `DELETE` | `/announcements/{id}` | `department.announcement.view` / `.update` / `.delete` | `Announcement` / 204 | `UC-DEPT-003`, `BR-DEPT-004`, `AFR-DEPT-004..006` |
| `POST` | `/announcements/{id}/hide` | `department.announcement.update` | `Announcement` | `UC-DEPT-003`, `BR-DEPT-004`, `AFR-DEPT-005` |
| `GET` / `POST` | `/inventory` | `department.inventory.view` / `.create` | `InventoryItem` | `UC-DEPT-019`, `BR-DEPT-016`, `AFR-DEPT-007`, `008`, `014` |
| `GET` / `POST` | `/stock-requests` | `department.stock_request.view` / `.create` | `StockRequest` | `UC-DEPT-004`, `BR-DEPT-005`, `015`, `AFR-DEPT-009`, `010`, `041`, `042` |
| `POST` | `/stock-requests/{id}/decide` | `department.stock_request.approve` | `StockRequest` | `UC-DEPT-005`, `BR-DEPT-006`, `AFR-DEPT-011`, `043`, `CW-DEPT-01` |
| `POST` | `/stock-requests/{id}/issue` | `department.stock_request.update` | `StockRequest` | `UC-DEPT-006`, `BR-DEPT-007`, `016`, `AFR-DEPT-012`, `013`, `015`, `043` |
| `GET` | `/stock-movements` | `department.stock_movement.view` | Paginated `StockMovement` | `UC-DEPT-011`, `BR-DEPT-012`, `016`, `AFR-DEPT-014..016` |
| `GET` / `POST` | `/feedback` | `department.feedback.view` / `.create` | `Feedback` | `UC-DEPT-007`, `BR-DEPT-008`, `017`, `AFR-DEPT-017`, `018`, `044` |
| `POST` | `/feedback/{id}/review` | `department.feedback.review` | `Feedback` | `UC-DEPT-008`, `BR-DEPT-018`, `AFR-DEPT-019..021`, `CW-DEPT-02` |
| `POST` | `/feedback/{id}/dispose` | `department.feedback.update` | `Feedback` | `UC-DEPT-008`, `UC-DEPT-014`, `BR-DEPT-009`, `018`, `AFR-DEPT-022`, `023`, `045` |
| `GET` / `POST` | `/timetables` | `department.timetable.view` / `.create` | `TimetableSlot` | `UC-DEPT-009`, `UC-DEPT-018`, `BR-DEPT-010`, `AFR-DEPT-029`, `031`, `037` |
| `PATCH` | `/timetables/{id}` | `department.timetable.update` | `TimetableSlot` | `UC-DEPT-009`, `BR-DEPT-010`, `AFR-DEPT-030`, `031` |
| `GET` / `POST` | `/labs` | `department.lab.view` / `.update` | `LabResource` | `UC-DEPT-011`, `UC-DEPT-017`, `BR-DEPT-012`, `AFR-DEPT-034`, `035` |
| `PATCH` | `/labs/{id}` | `department.lab.update` | `LabResource` | `UC-DEPT-017`, `AFR-DEPT-034` |
| `GET` / `POST` | `/programs` | `department.program.view` / `.update` | `DepartmentProgram` | `UC-DEPT-018`, `AFR-DEPT-036` |
| `PATCH` | `/programs/{id}` | `department.program.update` | `DepartmentProgram` | `UC-DEPT-018`, `AFR-DEPT-036` |
| `GET` / `POST` | `/profiles` | `department.profile.view` / `.update` | Role-projected `DepartmentProfile` | `UC-DEPT-015`, `UC-DEPT-016`, `BR-DEPT-019`, `AFR-DEPT-024..028` |
| `GET` / `PATCH` | `/profiles/{id}` | `department.profile.view` / `.update` | Role-projected `DepartmentProfile` | `UC-DEPT-015`, `UC-DEPT-016`, `BR-DEPT-019` |
| `GET` / `POST` | `/roster` | `department.profile.view` / `department.roster.update` | `CourseEnrollment` | `BR-DEPT-019`, `AFR-DEPT-026` |
| `GET` / `POST` | `/role-assignments` | `department.role_assignment.view` / `.assign` | `DepartmentRoleAssignment` | `UC-DEPT-020`, `BR-DEPT-021..023`, `AFR-DEPT-047`, `048`, `051`, `052` |

**Client routes & guards** (1:1 parity with `NAV_ITEMS`):
- `announcements` → `RequirePermission("department.announcement.view")`
- `inventory` → `RequirePermission("department.stock_request.view")`
- `feedback` → `RequirePermission("department.feedback.view")`
- `timetable` → `RequirePermission("department.timetable.view")`
- `resources` → `RequirePermission("department.lab.view")`
- `profiles` → `RequirePermission("department.profile.view")`
- `details` → `RequirePermission("department.department.view")`
- `roles` → `RequirePermission("department.role_assignment.view")`

**`Fusion-client` `INTEGRATED_MODULES` entry (for `full-platform` handover):**
```js
{ id: "department", label: "Department", icon: "Buildings", to: "/department", section: "Department" }
```

## Step 3.6 (f) — Contracts

**Exposed by `modules/department/contracts.py` (all plural by signature):**
- `get_departments(department_ids: Sequence[int]) -> dict[int, DepartmentDTO]`
- `get_active_role_holders(department_ids: Sequence[int]) -> dict[int, DepartmentLeadershipDTO]`
- `get_inventory_items(item_ids: Sequence[int]) -> dict[int, InventoryItemDTO]`

**Consumed from other modules:**
- `modules/directory/contracts.py`: `get_users(user_ids)`, `search(...)` (no changes required to `directory`).

## Step 3.7 (g) — Scheduled work

Exported from `modules/department/schedule.py` and merged into `config/celery.py`:
1. `department.apply_role_transitions` (every 60s, queue `default`, expires 55s): executes `UC-DEPT-022` / `BR-DEPT-024` — activates scheduled HOD/Dept_Admin assignments whose `valid_from <= now`, supersedes outgoing holders, expires ended assignments, and synchronizes `Department.active_hod_user_id` (`AFR-DEPT-053`). If it stops running, scheduled role handovers and Headship updates do not take effect on time.
2. `department.deliver_notifications` (every 60s, queue `notifications`, expires 55s): drains pending `DepartmentNotification` rows (`AFR-DEPT-041..046`). If it stops running, stock/feedback/announcement notifications queue up undelivered.

## Step 3.8 (h) — Open questions and accepted gaps

1. **Live IAM/ERP designation mutation (`BR-DEPT-024`):** Under ADR-0002/ADR-0014, `fusion_integrated` never writes to `fusionlab` or IAM, and `IamClient` has no designation-mutation endpoint. `modules/department` enforces time-bounded role assignment, single-active cardinality, effective-date transition, and Headship derivation locally; live IAM/ERP designation projection remains an IAM-owned responsibility (accepted gap).
2. **Notification channel policy (`AFR-DEPT-041..046`):** Notifications are persisted in `DepartmentNotification` (in-app outbox) and drained via Django's configured email backend (`EMAIL_BACKEND`).
3. **Profile privacy field list (`BR-DEPT-019`):** `sensitive_personal_data` is structurally separated on `DepartmentProfile` and excluded from all API serializers; non-sensitive fields are tiered into Student Basic, Faculty Limited (Faculty/Alumni), Faculty Detailed (enrolled Students), and HOD/Dept_Admin Full-minus-sensitive.
4. **Non-negative inventory at issuance (`BR-DEPT-015` / `UC-DEPT-006`):** In addition to request-time validation (`BR-DEPT-015`), issuance enforces a non-negative stock check under `select_for_update` backed by a DB `CheckConstraint(current_quantity >= 0)` so concurrent requests cannot drive inventory negative.
