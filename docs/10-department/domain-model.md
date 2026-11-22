# Department Module — Domain Model and State Machines

## Bounded Context

The `department` module owns department-scoped administration inside `Fusion-Integrated`:

- **Announcements (`Announcement`)**: targeted by role, program, and academic year (`BR-DEPT-001`..`004`).
- **Inventory and Stock Requests (`InventoryItem`, `StockRequest`, `StockMovement`)**: append-only movement ledger (`BR-DEPT-016`), request-time availability validation (`BR-DEPT-015`), HOD approval (`BR-DEPT-006`), and Dept_Admin issuance with non-negative stock enforcement (`BR-DEPT-007`).
- **Confidential Feedback (`Feedback`, `FeedbackTransition`)**: confidential submission (`BR-DEPT-008`, `BR-DEPT-017`), mandatory Dept_Admin initial review (`BR-DEPT-018`), and Dept_Admin/HOD terminal disposition (`BR-DEPT-009`).
- **Timetables, Labs, and Academic Programs (`TimetableSlot`, `LabResource`, `DepartmentProgram`)**: conflict-free slot validation (`BR-DEPT-010`) and Faculty/Student views (`BR-DEPT-012`, `UC-DEPT-018`).
- **Department Profiles and Course Roster (`DepartmentProfile`, `CourseEnrollment`)**: role- and relationship-scoped profile projection (`BR-DEPT-019`) with `sensitive_personal_data` structurally excluded from all API serializers.
- **Department Details and Official Changes (`Department`, `OfficialDetailChange`)**: general details editable by Dept_Admin; official fields (`name`, `core_policies`) require HOD approval (`BR-DEPT-011`, `BR-DEPT-013`). Headship (`active_hod_user_id`) is derived from the active HOD role assignment (`AFR-DEPT-053`).
- **Time-Bound Role Governance (`DepartmentRoleAssignment`)**: time-bounded HOD and Dept_Admin tenures (`BR-DEPT-021`..`024`) with a partial unique constraint enforcing at most one active holder per `(department, role_type)`.

## State Machines

```mermaid
stateDiagram-v2
    [*] --> pending_hod_approval : Faculty requests stock (UC-DEPT-004)
    pending_hod_approval --> approved_for_issuance : HOD approves (UC-DEPT-005)
    pending_hod_approval --> rejected : HOD rejects (UC-DEPT-005)
    approved_for_issuance --> issued : Dept_Admin issues (UC-DEPT-006)
```

```mermaid
stateDiagram-v2
    [*] --> new : Student or Faculty submits (UC-DEPT-007)
    new --> under_review : Dept_Admin reviews (UC-DEPT-008)
    new --> closed : Dept_Admin closes simple issue (UC-DEPT-008)
    under_review --> resolved : Dept_Admin or HOD resolves (UC-DEPT-008 / UC-DEPT-014)
    under_review --> closed : Dept_Admin or HOD closes (UC-DEPT-008 / UC-DEPT-014)
```

```mermaid
stateDiagram-v2
    [*] --> pending_hod_approval : Dept_Admin proposes official change (UC-DEPT-010)
    pending_hod_approval --> approved : HOD approves (UC-DEPT-012)
    pending_hod_approval --> rejected : HOD rejects (UC-DEPT-012)
```

```mermaid
stateDiagram-v2
    [*] --> scheduled : Institute Admin assigns role (UC-DEPT-020)
    scheduled --> active : System applies effective transition (UC-DEPT-022)
    scheduled --> cancelled : Institute Admin cancels
    active --> superseded : System activates incoming holder (UC-DEPT-022)
    active --> expired : System expires ended tenure (UC-DEPT-022)
```

## Deployment Order

1. `python manage.py migrate`
2. `python manage.py seed_departments`
3. `python manage.py seed_modules`
4. `python manage.py permission_manifest` and seed IAM via `seed_iam_permissions --manifest <path>`
5. `python manage.py check_department_readiness`
