# PHASE 2 LOG - ELM (Leave) module improvement

Branch: elm-gemma4-e4b-phase2 (from tag phase1-gemma-original, 251a171)

## STEP 0 - Preservation and environment check
- Branch: elm-gemma4-e4b-phase2 (verified)
- Tag phase1-gemma-original: present (verified)
- Backup ~/elm-pilot-PHASE1-ORIGINAL-backup: present (verified, untouched)
- Ollama: running, gemma4:e4b listed (verified)
- .phase2_specs: 7 spec files + ELM_SPEC_COMPACT.md present
- Created PHASE2_LOG.md and phase2_prompts/

## STEP 1 - Understand (inspection summary)
Specs read in full: 01 Problem Statement, 04 Business Rules, 06 Workflow Spec (all STTs), 02 FRS compact (all CFR/AFR).
Specs only outlined (headings/registries, content is derived by the compact files above): 03 Use Cases, 06 Traceability,
02 full FRS, ELM_SPEC_COMPACT. Spec conflicts found so far: none material (workflow v1.6 and BR v1.4 agree; Workflow v1.6 is
the latest and wins for states). Note: a retired BR-EL-021/026 and UC-006 exist and are intentionally unimplemented.

Integration facts (verified in code):
- leave is in `DOMAIN_MODULES` (config/settings/base.py:93), app label `leave_management`, `seed_modules` registers it.
- `config/urls.py` mounts directory + placement only. Leave has NO URL mount -> `/api/v1/leave/...` returns 404 (placement returns 401).
- Permission manifest check is a *grep* for permission strings in non-registry/non-test/non-selectors code. A permission only counts
  as enforced if it really is passed to HasPermission / checked in a service; I will verify enforcement by tests, not by the grep.
- ROLE_GRANTS keys must be IAM designation names (`globals_designation`). Leave uses placeholders `employee`, `manager`, `admin`.
  Real designations seen in docs/02-iam: Dean Academic, HOD (CSE), acadadmin, Registrar, Junior Assistant, student, placement_*.
  The IAM is an external service (IAM_BASE_URL 127.0.0.1:8001), not available here -> login/role assignment can only be verified with
  test stubs (as placement tests do), not live. Recorded as a limitation.
- Org hierarchy (Unit Head, Director, Establishment, hierarchy config) has no source in Fusion base besides IAM designations.

## STEP 2 - Build and run (evidence)
- Python 3.12.13 venv exists; Postgres 14 running locally (pg_isready: accepting connections); Docker daemon not running (not needed).
- `manage.py check`: clean. `manage.py migrate`: nothing to apply (leave_management.0001_initial already applied).
- `manage.py seed_modules`: registered placement_cell, leave_management.
- `runserver 127.0.0.1:8002`: /healthz -> {"status":"ok"}; /api/v1/leave/applications -> 404 (no API); /api/v1/placement/applications -> 401.
- Client: `npm run typecheck` ok, `npm test` 35 passed, `npm run build` ok. No leave pages exist in client/src/modules.
- No environment fixes were required.

## STEP 3 - Baseline tests and static analysis
- `make test`: **379 passed, 1 failed** (matches expectation). Failure: test_the_committed_manifest_matches_the_registries:
  7 permissions (application.create/delete/review/view/view_self, balance.manage/view) declared+granted but enforced nowhere.
- `ruff check .`: 34 errors, ALL in modules/leave (19 W293, 5 UP006, 4 E501, 3 UP035, 2 I001, 1 F401).
- `lint-imports`: 4 contracts kept, 0 broken. ops/checks: no_cross_module_fk OK, contracts_are_plural OK,
  **nav_matches_routes FAILS** (/leave/mine and /leave/new have no client route). `schema-check`: OK (no leave endpoints).
- No `leave` tests exist (0 collected). No bandit/semgrep configured in repo; ruff "S" (bandit) rules are enabled and report nothing in leave.
- Security scan of what exists: no endpoints, so no attack surface yet; models use plain user_id ints (consistent with Fusion convention).

## STEP 4 - Gap table (requirement -> status -> location)
Legend: IMPL = implemented, PART = partial, WRONG = incorrect, MISSING = missing.
| # | Requirement / rule (spec ref) | Status | Code location / note |
|---|---|---|---|
| 1 | Leave categories CL,RH,SCL,EL,COL,VL (BR-EL-001, AFR-002.2) | PART | models.LeaveCategory; CODE_CHOICES labels COL as "Casual Leave" (wrong) and are not used on the `code` field; no seed data |
| 2 | Entitlements CL8 RH2 SCL15 EL30 COL20 VL60 (BR-002..009) | PART | rules.get_annual_entitlement hard-codes numbers; ignores faculty/non-faculty (EL for faculty, VL for non-faculty both wrong); unknown code -> 0 silently; not config-driven (BR-030) |
| 3 | Continuous-day counting only EL/COL/VL; not CL/SCL/RH (BR-011) | WRONG | rules.calculate_leave_days ignores category; verified CL Fri->Mon = 4.0 |
| 4 | Half-day CL = 0.5, first/second half (BR-010) | WRONG | no first/second-half field; half-day on a multi-day range returns 2.0; half-day on non-CL accepted |
| 5 | Date validation (end >= start) (CFR-003) | WRONG | end<start returns 0.0 silently |
| 6 | Non-overlap incl. half-day exception (BR-012) | WRONG | check_half_day_exception: half-day inside an existing multi-day leave returns False (overlap missed); no halves modelled |
| 7 | VL->EL 2:1 incl. fractions (BR-007) | PART | rules.convert_vl_to_el correct for positives; negative input yields negative EL |
| 8 | Year-end processing (UC-020, BR-002..009) | MISSING | no service/command |
| 9 | Application model & lifecycle states (Workflow v1.6) | WRONG | LeaveApplication.STATUS_CHOICES copied from placement (shortlisted, interview_scheduled, offer_*); no `status` field at all; no substitute, recommendation, kind (new/cancel/extension), approved-through fields |
| 10 | One application per category per user | WRONG | UniqueConstraint(category,user_id) forbids a second CL ever; also placement-isms (cpi_at_apply, semester_at_apply, standing_declared_seq_at_apply) |
| 11 | Transition audit (CFR-016.4) | PART | LeaveApplicationTransition exists but has `actor_recruiter_id` (placement-ism), no state machine writes it |
| 12 | LeaveBalance model | PART | unique (category,user,year) ok; no ledger/transactions; decimal(5,2) ok; `user_id` redeclared |
| 13 | Workflow state machine (BW-01..17, CW-01..04) | MISSING | no domain/state_machine.py |
| 14 | Substitute nomination/consent/decline loop (BR-014/015) | MISSING | |
| 15 | Unit Head final CL/RH; recommend for SCL/EL/COL/VL (BR-016/017) | MISSING | |
| 16 | Higher-sanction routing, Establishment optional, Director self-sanction (BR-018..020) | MISSING | |
| 17 | Withdraw pending (BR-022/034) | MISSING | permission declared, nothing enforces it |
| 18 | Cancel approved leave pre-start + balance restore (BR-023/024) | MISSING | |
| 19 | Extension of ongoing EL/COL/VL, incremental post (BR-025) | MISSING | |
| 20 | Resumption normal/early/late (BR-027/028) | MISSING | |
| 21 | Offline-sanctioned entry / admin record maintenance (BR-029/037) | MISSING | |
| 22 | Role-based authorisation (BR-036) | MISSING | registry.py declares permissions but no endpoint enforces; roles are placeholders |
| 23 | API (apply, list, decide, balances) / serializers / urls | MISSING | no api/ package; not mounted in config/urls.py |
| 24 | Balances & history view (CFR-022) | MISSING | |
| 25 | Printable/exportable application (CFR-023) | MISSING | |
| 26 | Holiday/RH calendar + publish (BR-003/031, CFR-025) | MISSING | no model |
| 27 | Policy/hierarchy/SLA configuration (BR-030/038) | MISSING | |
| 28 | Notifications / SLA reminders / escalation (BR-032/033/035) | MISSING | out of practical scope; to be logged as limitation |
| 29 | Frontend pages | MISSING | nav items point at /leave/mine and /leave/new, no client routes (nav_matches_routes fails) |
| 30 | Tests | MISSING | 0 leave tests |
| 31 | Lint | PART | 34 ruff errors in leave |

## STEP 4 - Prioritised issue list (all verified by reading code or by the probe in scratch/probe_rules.py)
CRITICAL
- C1 No API/service layer: none of the employee/approver/admin workflows can be exercised (gap rows 13-24). 404 on /api/v1/leave/.
- C2 LeaveApplication has no `status` field and its declared choices are placement states; the workflow cannot be represented (row 9).
- C3 UniqueConstraint(category,user_id) blocks a user from ever applying for a category twice (row 10).
- C4 Overlap check misses a half-day inside an existing multi-day leave (row 6) -> double-booking possible.
- C5 Permissions declared but unenforced; ROLE_GRANTS use placeholder designations (row 22).
HIGH
- H1 Day counting ignores category (BR-EL-011) -> wrong chargeable days / balance (row 3).
- H2 Half-day semantics wrong (row 4). H3 No date validation (row 5).
- H4 Entitlement ignores faculty/non-faculty and unknown category -> 0 (row 2).
- H5 Year-end, withdraw, cancel, extension, resumption, substitute, routing all missing (rows 8, 14-21).
MEDIUM
- M1 COL labelled "Casual Leave"; CODE_CHOICES unused (row 1). M2 placement-isms in models (CPI, recruiter) (rows 10, 11).
- M3 convert_vl_to_el accepts negatives (row 7). M4 No seed data for LeaveCategory.
- M5 nav_matches_routes check fails; no frontend (row 29).
LOW
- L1 34 ruff findings. L2 Calendar/SLA/notification features absent (rows 26-28) - scoped out, to be listed as limitations.


## STEP 5.1 - domain/rules.py (issues C4, H1, H2, H3, H4, M3)
- Design (human, from spec): new pure-Python API (RuleViolation, CATEGORIES, get_annual_entitlement(is_faculty), calculate_leave_days(
  category, start, end, half_day, holidays), check_overlap(existing(start,end,half), ..., new_half), convert_vl_to_el, has_sufficient_balance,
  carry_forward_amount). Old check_half_day_exception removed (folded into check_overlap, BR-EL-012).
- Prompts / Gemma attempts:
  - 01_rules_tests.md (tests first) - attempt 1: success with blemishes (dead code in one test, unused fixture).
  - 01b_rules_tests_cleanup.md - attempt 1: success.
  - 02_rules_impl.md (implementation) - attempt 1: success, 36/36 tests passed first run; reviewed diff, logic matches BR-EL-007/010/011/012.
  - Mutation testing (temporary sed mutants, restored after): 4 mutants; 3 killed, 1 survived (VL/COL/SCL/RH counting untested).
  - 01c_rules_tests_all_categories.md - attempt 1: success; mutant now killed. Final: 43 rule tests.
- Evidence: `pytest modules/leave` 43 passed; full `pytest` 422 passed / 1 failed (same manifest failure, expected until 5.5); `manage.py check` clean;
  lint-imports 4 kept (domain stays Django-free).
- Verified fixes: CL Fri->Mon now 2 (was 4); half-day inside multi-day leave now overlaps (was missed); end<start raises; unknown category raises;
  faculty/non-faculty EL/VL entitlements.
- Open: ruff style findings in rules.py/test_rules.py (whitespace, typing.List) - to be cleaned by a Gemma lint prompt in 5.8.
- Not covered: holiday/RH calendar source (holidays param is supplied by caller; no calendar model yet).
