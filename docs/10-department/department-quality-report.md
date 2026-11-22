# Department Module — Quality Report

## 1. CI Gates (`make check` and `make check-client`)

### Backend (`make check`)
```text
.venv/bin/python manage.py check -> System check identified no issues (0 silenced).
.venv/bin/python manage.py makemigrations --check --dry-run -> No changes detected
.venv/bin/ruff check . -> All checks passed!
.venv/bin/lint-imports -> Analyzed 256 files, 825 dependencies. Contracts: 5 kept, 0 broken.
.venv/bin/python ops/checks/no_cross_module_fk.py -> no cross-module foreign keys
.venv/bin/python ops/checks/contracts_are_plural.py -> all contract getters are plural
.venv/bin/python ops/checks/nav_matches_routes.py -> nav items and client routes agree
.venv/bin/python manage.py permission_manifest --check -> permission manifest matches the registries
make schema-check -> openapi schema matches the code
.venv/bin/python -m pytest -q -> 100% passed (exit code 0)
```

### Frontend (`make check-client`)
```text
npm run typecheck -> tsc --noEmit (0 errors)
npm test -> vitest run (13 test files passed, 45 tests passed)
npm run build -> built in 2.15s (largest department page chunk: InventoryPage 1.55 kB gzip, well under 150 kB gzip)
```

## 2. Branch Coverage (Step 5.14)

- Production code (`modules/department`, omitting `*/tests/*,*/migrations/*`):
  - Command: `.venv/bin/pytest modules/department --cov=modules/department --cov-branch --cov-report= && .venv/bin/coverage report --omit="*/tests/*,*/migrations/*" --fail-under=90`
  - Result: **94% branch coverage** (2,063 stmts, 80 miss, 358 branches, 64 partial; 50 tests passed).
- Pure domain (`modules/department/domain`):
  - Command: `.venv/bin/pytest modules/department/tests/test_domain.py --cov=modules/department/domain --cov-branch --cov-report=term-missing --cov-fail-under=95`
  - Result: **99.29% branch coverage** (213 stmts, 1 miss, 70 branches, 1 partial; 11 tests passed).

## 3. Test Counts and Use-Case Journey Coverage

| Test File | Tests | Scope |
|---|---|---|
| `test_domain.py` | 11 | Pure Python domain rules & exhaustive state-machine transition matrices |
| `test_journeys.py` | 8 | End-to-end HTTP journeys covering all 20 live UCs (`UC-DEPT-001`..`012`, `014`..`020`, `022`) + plain student |
| `test_privilege_escalation.py` | 7 | Dual gates, 401/403/400, role-switch isolation, self-approval guards, CSRF enforcement |
| `test_scoping_isolation.py` | 4 | Cross-department 404 isolation, feedback confidentiality & HOD initial-review gate, faculty stock isolation, profile visibility & sensitive PII exclusion |
| `test_concurrency.py` | 2 | Real-thread `Barrier` stock issuance race + DB partial unique constraint for single active HOD |
| `test_query_budgets.py` | 7 | Constant query count (2 rows vs 12 rows) across all 7 list endpoints |
| `test_schedule.py` | 4 | Celery beat registration, queue routing, task idempotency, management commands, plural contracts |
| `test_edge_cases.py` | 6 | Inventory top-up, duplicate conflicts, 404/409/400 error paths, role expiry, notification retry failure, 429 throttling |
| `test_client_route_guards.py` | 1 | Pins every client route guard in `routes.tsx` against `registry.NAV_ITEMS` |

Frontend tests (`client/src/modules/department/`): `api/hooks.test.tsx` (2 tests) + 8 page test suites (`AnnouncementsPage`, `InventoryPage`, `FeedbackPage`, `TimetablePage`, `ResourcesPage`, `ProfilesPage`, `DetailsPage`, `RolesPage`), each testing loading, empty, 500 error, permission-gated control absence, and main form action.

## 4. Five Broken-on-Purpose Rules Caught by Tests (Step 5.15)

| # | Mutated Rule | Caught By |
|---|---|---|
| 1 | Scoping filter (`BR-DEPT-017`/`018`: removed HOD `under_review`/`resolved`/`closed` filter in `selectors/scoping.py`) | `test_scoping_isolation.py::test_feedback_confidentiality_and_hod_initial_review_gate` |
| 2 | Permission gate (removed `HasPermission("department.department.view")` on `DepartmentListView`) | `test_privilege_escalation.py::test_both_gates_enforced_separately_and_unauthenticated_is_401` |
| 3 | Stock availability limit (`BR-DEPT-015`: disabled `requested_quantity > current_quantity` in `domain/rules.py`) | `test_journeys.py::test_uc_dept_004_005_006_011_019_stock_approved_and_rejected_journeys` |
| 4 | State transition guard (`BR-DEPT-007`: allowed `STOCK_PENDING -> STOCK_ISSUED` in `domain/state_machine.py`) | `test_edge_cases.py::test_state_conflict_and_404_error_paths` |
| 5 | Timetable conflict check (`BR-DEPT-010`: forced `overlaps = False` in `domain/rules.py`) | `test_journeys.py::test_uc_dept_009_017_018_timetable_labs_and_programs` |

## 5. Adversarial Pass (Step 5.11)

- **Can an approver approve their own record?** Checked and blocked (`409 self_approval_forbidden`) for HOD stock-request approval, HOD official-change approval, and Dept_Admin/HOD feedback review/disposition.
- **Can a balance go negative under concurrent issuance?** Checked with real threads on `threading.Barrier` (`test_concurrency.py`); locked via `select_for_update()` on `InventoryItem` and backstopped by DB `CheckConstraint(current_quantity >= 0)`.
- **Can Dept_Admin bypass initial review via `/dispose`?** Discovered during edge-case testing that `dispose_feedback` could match `(new, closed)` via the state table; fixed by explicitly rejecting `status == "new"` in `dispose_feedback` (`BR-DEPT-018`).
- **Can someone edit Headship via official department change?** Blocked in `domain/rules.py::validate_official_change_field` and DB `CheckConstraint(field_name__in=["name", "core_policies"])` (`AFR-DEPT-053`).
- **Can someone act on another department's rows by passing its `department_id`?** Every write service calls `require_department(actor, department_id)` backed by `selectors/scoping.py::departments_for(actor)`, returning `404`.
- **Can `sensitive_personal_data` leak to HOD/Dept_Admin?** Structurally excluded from `ProfileSnapshot` and every serializer (`BR-DEPT-019`).

## 6. Security Self-Audit (Step 7.7)

- All 25 endpoints sit behind `HasModuleGrant("department")` and `HasPermission(...)`; zero `AllowAny`.
- All serializers declare explicit fields (no `__all__` or `exclude`); all server-owned fields are `read_only=True`.
- All reads and writes narrow through `selectors/scoping.py` (out-of-scope returns 404).
- Zero raw SQL, `.extra()`, `eval`, `pickle`, `yaml.load`, or `subprocess` on request data.
- All write endpoints carry `throttle_scope` (`dept_write`, `dept_feedback`, `dept_role_assign`); 429 verified in tests.
- Cookie-authenticated write without `X-CSRF-Token` returns `403` (`test_cookie_write_without_csrf_token_returns_403`).
- Client uses shared `lib/http.ts`, zero `dangerouslySetInnerHTML`, zero `localStorage` tokens, zero `any`/`@ts-ignore`/`console.log`.
- Production deploy check (`DJANGO_SETTINGS_MODULE=config.settings.prod ... manage.py check --deploy --fail-level WARNING`): `System check identified no issues (2 silenced).`

## 7. Fresh-Install Proof (Step 7.8)

Executed against throwaway Postgres database `fusion_integrated_fresh` (then dropped):
```text
migrate -> Applying department.0001_initial... OK
migrate department zero -> Unapplying department.0001_initial... OK
migrate -> Applying department.0001_initial... OK
seed_modules -> department: registered but NOT active — 1 prerequisite(s) unmet: No departments exist yet. Run `python manage.py seed_departments` to create them.
check_department_readiness -> CommandError: Department module has 1 unmet prerequisite(s).
seed_departments -> Seeded departments (7 created, 7 total).
seed_modules -> registered department (active) / 2 module(s) registered
check_department_readiness -> Department module is ready.
run_department_tasks -> Department tasks complete: 0 role transition(s), 0 notification(s) delivered.
```

## 8. Browser Walkthrough & Playwright E2E (Step 6.9)

- **Status:** Not run in this session (live IAM/backend/Vite dev servers are not running and `client/e2e/` Playwright harness is not present on `main` `02b01fe`).
- All 8 frontend pages and route guards are verified in Vitest (`make check-client`) and `test_client_route_guards.py`.

## 9. Scheduled Tasks Run by Hand

- `python manage.py run_department_tasks` executed on `fusion_integrated_fresh`: `Department tasks complete: 0 role transition(s), 0 notification(s) delivered.`
- Both tasks (`department.apply_role_transitions`, `department.deliver_notifications`) verified idempotent in `test_schedule.py::test_scheduled_tasks_are_idempotent`.

## 10. Accepted Known Gaps (Step 3.8 h)

1. **`BR-DEPT-024` live IAM/ERP designation mutation:** `Fusion-Integrated` cannot write to `fusionlab` or mutate IAM designations (ADR-0002/ADR-0014); local tenure, cardinality, effective transition, and Headship derivation are enforced in `modules/department`.
2. **Portal sidebar registration (`Fusion-client`):** In `module-only` environment, `Fusion-client` is not checked out; exact `INTEGRATED_MODULES` entry is documented in `docs/10-department/department-blueprint.md` Step 3.5 (e).
3. **IAM seeding (`seed_iam_permissions`):** `registry/permissions.json` is regenerated and verified by `permission_manifest --check`; run `seed_iam_permissions --manifest /Users/siddharthilayaraja/Documents/Fusion/Fusion-Integrated/registry/permissions.json` from `Fusion_System_Administrator/Backend/backend` when starting the IAM service.
