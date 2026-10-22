# Tasks: Student Self-Enrollment

**Input**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md),
[data-model.md](data-model.md), [enrollment contract](contracts/enrollment-api.md),
[student contract](contracts/student-details.md), [quickstart.md](quickstart.md),
and Constitution v2.0.0.

**Organization**: Two P1 stories: US1 Student Self-Enrollment and US2 Valid Student
Details. T001–T050 below preserve the historical delivery record and checked markers.
T051–T094 record the completed pre-amendment delivery. Phase 10 (T095–T100) completed final verification of the amended Unicode acceptance suite; T100 passed on 2026-10-22. T050 was reassessed and completed during final validation
under Constitution v2.0.0. IDs remain stable; original execution evidence is preserved. Existing source/tooling edits
must be inspected and retained where compatible rather than overwritten.

## Active execution rules

All tasks T001–T100 are complete; no unchecked tasks remain. T001–T094 record the
pre-amendment delivery, and Phase 10 (T095–T100) verified the Unicode acceptance
amendment, with T100 passing evidence validation for the amended digest. T090–T094 completed the T050 reassessment under Constitution
v2.0.0, as recorded in the final implementation outcome below. These execution rules
remain applicable to future changes. Historical task descriptions are archival and
MUST NOT be executed or used as active implementation instructions. T050 MUST NOT
be executed from its archival description or used to reinstate superseded process
requirements. Historical dependencies, strategies and traceability sections are
reference material only.

Acceptance tests guide Outside-In TDD in cohesive behavioral increments. For each
increment, execute relevant tests that fail for the expected behavioral reason before
implementation, implement the required behavior and verify relevant tests pass, then
consider refactoring and verify relevant tests remain passing. Related behaviors may
share a cycle and tests may span layers through a shared behavioral boundary. Separate
cycles per assertion, branch or independently testable behavior are not required.
Configuration, constructor, import, environment and schema setup failures are not
behavioral Red. Do not weaken tests
or break correct behavior to manufacture failures. Pure refactors start from passing
relevant tests and verify them afterward; no code change is required when unwarranted.

Retain lightweight commands/results showing relevant Red before implementation and
Green afterward. Evidence may be consolidated across increments; no fixed increment
inventory, intermediate snapshots, per-behavior approval or separate no-refactor
artifact is mandatory. Passing tests or coverage alone do not establish TDD. Do not
mark new behavioral work done without its relevant passing checks and actual execution
evidence. Preserve historical execution files unchanged and record new reviews separately.

Coverage has two distinct levels: the constitutional floor is 100% branch coverage of
each whole affected business-logic function/method, including unchanged branches;
the retained approved project gate is 100% statement and branch coverage across all
Domain/Application source, including unimported modules and business logic elsewhere.
Do not lower scope/thresholds or add business exclusions. All acceptance/regression,
contract, architecture and static checks remain mandatory on the final state.

`[P]` denotes disjoint files after stated prerequisites. Story tasks carry `[US1]` or
`[US2]`. Each new behavioral task includes test-first execution, required implementation
and passing verification as a cohesive unit; a task boundary is not a mandated cycle
for every listed branch. Paths are repository-relative.

## Historical delivery record — T001–T050

The following original descriptions, historical claims and statuses are retained for
traceability only. All historical task descriptions, dependencies and strategies are
archival and MUST NOT be executed or used as active implementation instructions.
Historical test totals are not current results. T050 was pending at this historical
stage; T090–T094 subsequently completed its evidence-based reassessment and final
validation under Constitution v2.0.0. Grouping alone is
not a violation under v2.0.0; neither historical failure nor final Green automatically
settles current compliance. Original review/output remains unchanged.

## Phase 1: Setup (shared infrastructure)

**Purpose**: Create packaging and verification configuration, with no business behavior.

- [X] T001 Create Python package/test directories and inert package initializers in src/enrollment/__init__.py, src/enrollment/domain/__init__.py, src/enrollment/application/__init__.py, src/enrollment/adapters/__init__.py and tests/conftest.py; preserve the plan's adapter subpackages and add no business implementations.

- [X] T002 Configure pyproject.toml for Python ">=3.12,<3.13", graphql-core ">=3.3,<3.4", Flask ">=3.1,<3.2", Waitress, pytest, HTTPX, coverage.py, mypy, Ruff and Import Linter; resolve stable compatible releases into uv.lock and validate uv sync --frozen --dev --python 3.12. Explicitly select Hatchling as the single Python build backend: provide a valid PEP 517 [build-system] table declaring hatchling in requires and build-backend = "hatchling.build". Configure [tool.hatch.build.targets.wheel] with packages = ["src/enrollment"] for the existing src layout and ensure both src/enrollment/adapters/graphql/schema.graphqls and src/enrollment/adapters/persistence/schema.sql are included at their package-relative paths. Use package-resource loading rather than checkout-relative paths; no additional packaging service, backend or Hatch CLI workflow is required.

- [X] T003 [P] Add repository artifact exclusions in .gitignore for .venv, Python caches, coverage reports and test/build output while retaining feature evidence transcripts for review.

- [X] T004 [P] Document execution capture, stage ordering, code/diff digest rules, retention and no-refactor records in specs/001-enroll-course/evidence/README.md; define a manifest format that records failures and cannot claim a missing check passed.

- [X] T005 Configure pyproject.toml with pytest discovery, Python-3.12 strict mypy plus warn_unused_ignores/warn_unreachable/disallow_any_unimported, Ruff E4/E7/E9/F/I/B/UP and format checks, and coverage branch=True/fail_under=100 across complete Domain/Application source directories including unimported files; reject business exclusions.


## Phase 2: Foundational (blocking prerequisites)

**Purpose**: Build only test plumbing and architecture gates before US1. No authorization, eligibility, repository-miss or persistence behavior is implemented here.

- [X] T006 Create fixture plumbing in tests/conftest.py and tests/support/database.py for independent temporary SQLite files, prerequisite records, enrollment snapshots and connection reopen assertions; use raw fixture data until real Domain types exist and do not add prerequisite-management APIs.

- [X] T007 Create an inert Flask app factory shell in src/enrollment/adapters/http/app.py and composition shell in src/enrollment/bootstrap.py, with fixtures in tests/support/application.py; make imports/startup work but leave the enrollment route unimplemented so US1 assertions can fail for missing observable behavior. Test doubles must never fabricate successful enrollment.

- [X] T008 Write architecture fitness tests in tests/architecture/test_boundaries.py and violating fixtures in tests/architecture/fixtures/ covering inward dependencies, public type/annotation/re-export isolation, no Flask/Werkzeug/graphql/sqlite3/provider types in Core, no Domain import of Application ports/results, allowed direct adapter-to-Domain construction and the declared HTTP-to-GraphQL pipeline; fail empty production scope once business files exist.

- [X] T009 Configure Import Linter contracts in pyproject.toml for bootstrap -> adapters -> application -> domain, forbidden external imports including annotation imports, independent outbound adapters and Flask-free GraphQL execution; run the fitness tests with violating fixtures and retain detection evidence in specs/001-enroll-course/evidence/T009/. Do not confuse import checks with proof of conversion semantics or predicate ownership.


**Checkpoint**: Packaging/fixtures/checks work; no business implementation has begun. Negative architecture fixtures must be detected. Final nonempty business coverage remains a blocking completion gate, not something to waive while Core is still empty.

## Phase 3: User Story 1 — Student Self-Enrollment (P1, MVP)

**Goal**: Persist exactly one eligible self-enrollment and return the first applicable rejection without attempt-caused enrollment mutation.

**Independent test**: Through Flask POST `/graphql`, exercise all fifteen specification scenarios with real graphql-core execution, file-backed SQLite and a deterministic identity double. Reopen the database to prove durability; prove ownership/persistence are never called on negative verification, verify all seven FR-009 stages, and run actual overlapping requests plus fault injection.

### Acceptance tests first

- [X] T010 [US1] Write the fifteen numbered HTTP acceptance examples and stable scenario IDs in tests/acceptance/test_enrollment.py using the SDL document/variables and credential headers; begin by executing scenario 1 and 13 assertions Red against the importable app shell. Add deterministic scheduling/fault hooks only to fixtures. Before each later behavior slice, execute its guiding acceptance assertion: require behavioral Red if that external behavior is unimplemented, otherwise preserve Green and drive the missing behavior with a genuinely failing focused inner test; never count a skipped scenario or configuration failure.


### Models and policies — driven from the acceptance failures

- [X] T011 [US1] Write and execute focused Red tests in tests/domain/test_values.py for distinct StudentId/ProgrammeId/CourseId/SubjectId classes and VerifiedIdentity: quote constraints "Identifiers are nonempty opaque strings, compared exactly, with no trimming/case folding" and "runtime checks for actual string type and nonempty value"; assert invalid construction/reconstitution and exact identity comparison inputs without requiring a verifier port or UnverifiedIdentity.

- [X] T012 [US1] Implement the tested value classes/VerifiedIdentity in src/enrollment/domain/values.py and shared Core Denied/policy result types in src/enrollment/domain/outcomes.py; use immutable scalar fields and validating constructors, preserving "Frozen fields do not deeply freeze mutable contents; these IDs hold immutable strings". Execute individual Red/Green/Refactor cycles before each behavior and do not add external imports.

- [X] T013 [US1] Write and execute Red tests in tests/domain/test_records.py for Student, Programme, Course, ProgrammeCourseOffering and Enrollment construction/reconstitution: "One referenced programme; a dangling programme reference must remain representable so MISSING_PROGRAMME can be returned", "May offer zero or more courses", "May be offered by zero or more programmes", "Immutable association; exactly one pair, no term dimension or synthetic identity required"; valid saved enrollments survive later offering/membership changes.

- [X] T014 [US1] Implement the tested records and Enrollment factory in src/enrollment/domain/models.py with the data-model field/key relationships: Student(student_id, programme_id), Programme(programme_id), Course(course_id), ProgrammeCourseOffering(programme_id, course_id), Enrollment(student_id, course_id); validate construction/reconstitution while never requiring a repository lookup or representing a missing record as an entity.

- [X] T015 [US1] Write and execute policy Red tests in tests/domain/test_policies.py for ownership(VerifiedIdentity, StudentId), duplicate-enrollment and offering eligibility, including shared courses, no offerings, existing pair and exact mismatch DENIED. Domain receives verified identities only; no trivial Student/Programme/Course None guards. Execute guiding acceptance scenarios 2, 7, 8, 12 and 14 before their respective increments: observe Red for unimplemented outcomes, otherwise preserve Green and use focused policy Red for the next missing behavior. Never manufacture a failure.

- [X] T016 [US1] Implement the tested policies in src/enrollment/domain/policies.py and src/enrollment/domain/outcomes.py, using separate callable duplicate/eligibility steps so eligibility is never invoked after duplicate rejection. Keep actor comparison and business predicates solely in Domain; Domain does not verify credentials, call IdentityVerifier or import Application types. Rerun focused tests and refactor with evidence.


### Application — verification, repository absence and FR-009 coordination

- [X] T017 [US1] Define neutral commands, Application-owned Protocol contracts and result type signatures in src/enrollment/application/contracts.py and src/enrollment/application/ports.py: IdentityVerifier returns VerifiedIdentity or None with a distinct provider-unavailable failure; UoW reads return validated Domain values or None and expose add/commit/rollback/close only. Missing-record types belong to Application; reuse Domain policy outcomes without redundant wrappers. Signatures introduce no production decisions.

- [X] T018 [US1] Write and execute Application Red tests in tests/application/test_identity.py: negative verification -> exact Core DENIED with zero ownership/persistence/target-ID construction; verified input -> validated target StudentId passed with trusted VerifiedIdentity; mismatch -> same DENIED; invalid StudentId after verification -> INVALID_REQUEST; invalid CourseId only after ownership. Provider outage -> IDENTITY_UNAVAILABLE, with no ownership/persistence.

- [X] T019 [US1] Implement verification and ownership orchestration in src/enrollment/application/enroll.py against T018, returning DENIED immediately on None and invoking Domain only for trusted identities. Add technical/invalid-input outcomes in src/enrollment/application/contracts.py; do not repeat the Domain identity comparison. Drive each branch separately and retain Red/Green/Refactor execution evidence.

- [X] T020 [US1] Write and execute Application Red tests in tests/application/test_prerequisites.py for scenarios 4–6: sequential Student -> Programme -> Course lookups, typed MissingStudent/MissingProgramme/MissingCourse and no later lookup/policy/write/commit on each miss. Verify a trusted matching identity can have no Student and missing records never imply offering ineligibility.

- [X] T021 [US1] Implement the tested missing-result handling in src/enrollment/application/enroll.py and rejection types in src/enrollment/application/contracts.py; return each Core rejection directly from Application without introducing Domain None guards or moving workflow into an adapter.

- [X] T022 [US1] Write and execute ordered-flow Red tests in tests/application/test_enrollment_flow.py for exact FR-009: unverified -> mismatch -> missing Student -> missing Programme -> missing Course -> already enrolled -> course not offered; test combined failures, policy-result propagation, no offering fetch/call after duplicate, commit-before-success and rollback/close on every rejected/failed transaction.

- [X] T023 [US1] Complete tested orchestration in src/enrollment/application/enroll.py: delegate duplicate and eligibility decisions, construct Enrollment through Domain, add once and explicitly commit before returning success. Do not duplicate policy predicates, eagerly load dependent facts or mutate prerequisite records; run per-branch inner TDD cycles and the guiding acceptance checks.


### Adapters and end-to-end integration

- [X] T024 [US1] Write and execute real-SQLite adapter Red tests in tests/adapters/test_sqlite.py and fixture-only schema setup in tests/support/database.py: quote "All IDs are NOT NULL TEXT with nonempty checks", composite primary keys for offerings/enrollments and "no cascading deletes into enrollments"; allow dangling Student programme reference. Test record/None reads, validated row conversion, corrupt-data failure, parameter binding, worker connection ownership and no prerequisite mutation methods.

- [X] T025 [US1] Implement schema setup and tested read/row bridges in src/enrollment/adapters/persistence/schema.sql and src/enrollment/adapters/persistence/sqlite.py. Preserve student/programme/course keys and offering/enrollment pair uniqueness, restrictive references where specified, and no student-to-programme FK that prevents scenario 5. Load schema.sql through importlib.resources from the installed package, not the repository working directory. Keep sqlite3 rows/exceptions out of Core; expose no record-management production API.

- [X] T026 [US1] Write and execute transaction Red tests in tests/adapters/test_transactions.py for Python 3.12 autocommit=True, SQL BEGIN IMMEDIATE before prerequisite reads, explicit SQL COMMIT/ROLLBACK and close, five-second configured lock timeout and confirmed commit visibility after reopen; verify rejection rollback does not delete an earlier enrollment.

- [X] T027 [US1] Implement tested UoW lifecycle/add/error bridges in src/enrollment/adapters/persistence/sqlite.py; use one connection in its creating worker, never connection.commit()/rollback() substitutes in autocommit=True, no nested BEGIN, global connection, INSERT OR REPLACE/IGNORE, or check_same_thread=False workaround. Drive error paths individually and rerun SQLite integration checks.

- [X] T028 [US1] Write and execute identity bridge Red tests in tests/adapters/test_identity_bridge.py for trusted provider success, invalid/absent credentials -> None, provider outage -> Core technical failure, no SDK/credential leakage and absent production verifier configuration failing closed. Use a callback/provider double; do not select or implement a new authentication provider.

- [X] T029 [US1] Implement the tested host-supplied verifier bridge in src/enrollment/adapters/identity/verifier.py and injection wiring in src/enrollment/bootstrap.py; the bridge implements Application IdentityVerifier, maps trusted provider output via validated Domain constructors and never queries Student. Production never accepts deterministic test credentials or a caller verified flag.

- [X] T030 [US1] Write and execute GraphQL contract Red tests in tests/adapters/test_graphql.py for build_schema/schema validation, mutation field binding, query placeholder, every result/enum/union mapping, exact camelCase keys, ID coercion/non-null/unknown fields, operationName/variables/context forwarding, no lazy reads and check_sync=True awaitable detection.

- [X] T031 [US1] Package the unchanged specs/001-enroll-course/contracts/schema.graphqls as src/enrollment/adapters/graphql/schema.graphqls and implement tested binding/execution/converters in src/enrollment/adapters/graphql/execution.py: explicit resolver delegates Application once, union resolver returns SDL type-name string, outputs contain enum names and trusted tags. Load schema.graphqls through importlib.resources from the installed package, wire schema once, keep per-request context separate and import no Flask proxies.

- [X] T032 [US1] Write and execute HTTP transport Red tests in tests/adapters/test_http.py for POST /graphql JSON and credentials, 404 paths, 405 GET/HEAD/OPTIONS with Allow: POST, 415 media types, malformed JSON/envelope 400, JSON status/header preservation, disabled static/automatic OPTIONS routes, expected union HTTP 200 and sanitized engine/internal failures in production-like error mode.

- [X] T033 [US1] Implement tested Flask factory/routes/error formatting in src/enrollment/adapters/http/app.py and assemble real Core/SQLite/identity/GraphQL dependencies in src/enrollment/bootstrap.py. Keep Flask/Werkzeug outside Core/execution context; views adapt requests only, never verify identities, perform repository checks or coordinate transactions. Use the real dependency graph to turn scenarios 1–2, 4–8 and 12–14 Green and verify subsequent-read durability.


### Race, retry and failure slices — acceptance-guided inner TDD

- [X] T034 [US1] Execute scenario 3 acceptance assertion under the Red/Green rule above and add deterministic inner tests in tests/acceptance/test_eligibility_races.py and tests/adapters/test_transactions.py: change commits before enrollment lock -> COURSE_NOT_OFFERED; writer arriving after BEGIN IMMEDIATE waits until enrollment commit; include both membership and offering changes with prerequisite records existing.

- [X] T035 [US1] Make only the changes driven by T034 in src/enrollment/application/enroll.py and src/enrollment/adapters/persistence/sqlite.py to preserve save-time facts throughout the same transaction. Use bounded events, never a two-worker barrier inside a single-writer critical section; rerun race assertions and relevant policies without adding new business rules.

- [X] T036 [US1] Execute scenario 10 and 15 acceptance assertions under the Red/Green rule above and add independent-worker tests in tests/acceptance/test_concurrency.py: same pair -> one success/one ALREADY_ENROLLED/one row; invalid attempt overlapping unrelated valid attempt -> only valid pair changes. Each thread owns its Flask client, context and connection; tests must prove overlap rather than sequential calls.

- [X] T037 [US1] Resolve only concurrency failures from T036 in src/enrollment/adapters/persistence/sqlite.py and src/enrollment/application/enroll.py; specifically classify pair uniqueness conflicts, rollback then perform at most one complete ordered re-evaluation, preserve higher-priority missing-record reasons and distinguish other integrity/storage failures. No unconditional duplicate mapping or unbounded retries; record per-behavior TDD evidence.

- [X] T038 [US1] Execute scenario 9 acceptance assertion under the Red/Green rule above and write tests in tests/acceptance/test_retry.py for lost response after actual commit, ordinary repeat -> ALREADY_ENROLLED, higher-priority missing-record rejection on retry and already-enrolled before offering. Use a controlled legacy fixture or port test when restrictive foreign keys prevent the combined persisted state; do not weaken production schema.

- [X] T039 [US1] Make only T038-driven corrections in src/enrollment/application/enroll.py and src/enrollment/adapters/graphql/execution.py: preserve committed enrollment after response/serialization loss, repeat the full normal precedence on retry and never compensate/update/delete the saved pair. Rerun retry and precedence suites; record no-change/no-refactor rationale if behavior is already proven.

- [X] T040 [US1] Execute scenario 11 acceptance assertion under the Red/Green rule above and add fault tests in tests/acceptance/test_persistence_failure.py and tests/adapters/test_transactions.py for failure during insert, before commit, at lock acquisition, rollback/close and ambiguous commit; assert no partial pre-commit row, no false success and no deletion after confirmed/possibly completed commit.

- [X] T041 [US1] Make only fault-driven corrections from T040 in src/enrollment/adapters/persistence/sqlite.py, src/enrollment/application/enroll.py and src/enrollment/adapters/http/app.py; distinguish corruption/storage failures from missing records, sanitize outward errors and preserve committed state. Fault seams belong to tests/adapter injection rather than business rules; complete focused Red/Green/Refactor evidence.

- [X] T042 [US1] Write and execute socket adapter Red tests in tests/adapters/test_server.py for Waitress serving the Flask app on an ephemeral local port with HTTPX, real simultaneous workers, debug disabled and deterministic cleanup; then add only necessary tested server wiring in src/enrollment/bootstrap.py. Do not deploy, use flask's development server as production, or add external services.

- [X] T043 [US1] Run all fifteen stable acceptance scenario IDs and inner suites from tests/acceptance/, tests/application/, tests/domain/ and tests/adapters/; verify no skipped examples, unchanged prerequisite snapshots and one first-match result. Close remaining failures using new behavioral Red/Green/Refactor cycles; record results in specs/001-enroll-course/evidence/T043/.


**Checkpoint**: US1 is independently functional through the declared public boundary. Success-only behavior is an interim demonstration, not the approved MVP: all rejection, durability, race and fault requirements belong to US1.

## Phase 4: Polish and cross-cutting completion gates

**Purpose**: Validate final-state enforcement and evidence; no new business scope.

- [X] T044 Validate installed package resources in tests/adapters/test_package_resources.py: build the wheel using the Hatchling PEP 517 backend established by T002 in pyproject.toml, install that wheel non-editably into a temporary isolated environment, remove checkout paths from PYTHONPATH and execute from a directory outside the repository. Using that environment's Python, prove importlib.resources.files("enrollment.adapters.graphql").joinpath("schema.graphqls") and importlib.resources.files("enrollment.adapters.persistence").joinpath("schema.sql") can read both resources from the installed artifact; compare expected contents and assert imported package/resource origins are inside the isolated installation rather than the repository or an editable mapping. Use uv, Hatchling and temporary directories/environments only; correct omissions in pyproject.toml/resource loaders as needed and rerun validation. A source-tree, checkout-dependent or editable-install check alone cannot pass this task.

- [X] T045 Prove whole-function coverage enforcement with controlled negative fixtures in tests/architecture/test_quality_gates.py, then implement/finish scripts/check-quality.sh to execute quality checks and capture raw commands, output, exit codes and source/config/test digest, and scripts/check_evidence.py to validate the manifest after assembly. Quality execution must not read or require a final manifest and must propagate failed checks; the later validator must reject absent/inconsistent evidence, stale digests, unimported business files, empty scope, skipped mandatory scenarios, unjustified suppressions and a missed branch. Test the sequence starting with no final manifest: checks can run, assembly follows, then validation passes only with complete matching evidence; missing or tampered results must fail closed. Gate tests themselves follow Red/Green/Refactor; do not add a custom per-function parser when complete-scope 100% already suffices.

- [X] T046 Audit actual production sources against ownership and boundary requirements in src/enrollment/domain/, src/enrollment/application/ and tests/architecture/test_boundaries.py: no Domain verifier/UnverifiedIdentity/trivial existence guards, no Application actor/duplicate/offering predicates, no external representations in Core. Add test-driven fitness/converter checks for real gaps; review semantic leakage that static imports cannot prove.

- [X] T047 Update runnable commands and host verifier/configuration requirements in README.md and specs/001-enroll-course/quickstart.md, including SQLite local-filesystem limitation, Flask factory/Waitress serving, no new business APIs, test client versus socket scope, locked dependency setup and installed-wheel resource validation. Explicitly document checks/capture -> manifest assembly -> evidence validation, with no pre-existing final manifest required to run quality checks; execute the documented validation steps.

- [X] T048 Execute final-state quality checks through scripts/check-quality.sh: tests including installed-wheel resource validation, architecture, Import Linter, strict mypy, Ruff lint/format and coverage report --fail-under=100. Capture raw commands/output/exit codes and the source/config/test digest under specs/001-enroll-course/evidence/final/checks/. This stage does not require or validate a final manifest. Preserve failed results; quality-stage success alone is not feature completion.

- [X] T049 Assemble specs/001-enroll-course/evidence/final/manifest.json only after T048 has captured results; include the exact source/config/test digest, references to raw check results, exit statuses, required scenario counts and increment Red/Green/Refactor evidence references. Record failures or missing results truthfully rather than dropping them or inventing a pass. Exclude evidence/build output from the code digest; assembly alone cannot declare completion.

- [X] T050 Execute scripts/check_evidence.py against specs/001-enroll-course/evidence/final/manifest.json after T049: validate completeness, cross-reference consistency, actual check results, required scenarios, increment evidence and digest freshness against the current source/config/tests. Fail closed on missing/failed/skipped/blocked mandatory checks, inconsistent references or stale state. Retain the validation result in specs/001-enroll-course/evidence/final/validation.json; reviewer inspects raw TDD transcripts. Any source/test/config edit requires repeating T048 -> T049 -> T050; declare feature completion only after all three stages and the review pass.


## Historical execution outcome (T001–T050)

The functional implementation and final quality capture pass: 148 tests, all fifteen numbered acceptance scenarios, 100% complete Core statement/branch coverage, strict mypy, Ruff and five Import Linter contracts. T048 captured raw results and T049 assembled the matching manifest.

**T050 was incomplete at this historical stage.** Evidence validation was executed and failed closed solely because the review did not pass. The original review rejected grouped Red suites followed by grouped implementations under the former per-behavior Red–Green–Refactor rule; checked delivery markers alone did not resolve that finding or establish completion. See the [original review](evidence/history/pre-reconciliation/review.json) and [original final validation](evidence/history/pre-reconciliation/final/validation.json). T090–T094 subsequently reassessed the retained execution evidence under Constitution v2.0.0 and completed T050; see the [current review](evidence/reconciliation/review.json) and [current final validation](evidence/final/validation.json). No historical result was rewritten or manufactured to claim compliance.

## Historical dependencies and execution order (T001–T050)

```text
T001 -> T002 -> (T003 || T004) -> T005
T005 -> T006 -> T007 -> T008 -> T009
T009 -> US1 acceptance Red T010
T010 -> values T011/T012 -> records T013/T014 -> policies T015/T016
     -> contracts T017 -> verification T018/T019 -> misses T020/T021
     -> ordering T022/T023 -> SQLite T024/T025 -> transactions T026/T027
     -> verifier bridge T028/T029 -> GraphQL T030/T031 -> Flask T032/T033
     -> eligibility race T034/T035 -> concurrency T036/T037
     -> retry T038/T039 -> fault T040/T041 -> server T042 -> US1 T043
T043 -> installed resources T044 -> final gate tooling T045 -> ownership audit T046
     -> docs T047 -> quality capture T048 -> manifest T049 -> evidence validation T050
```

Within each pair, execute tests Red before the corresponding production behavior. If an acceptance assertion is already Green because an earlier minimal implementation satisfied it, do not weaken it to manufacture Red; record that observation, and drive any genuinely unimplemented inner behavior with its own expected failure. Never manufacture Red when acceptance is already Green. No production correction is authorized solely because a task description anticipates one. Rerun coverage/evidence when scopes change.

The original scope contained only US1. Its tasks above remain historical; the Student extension below adds US2 and the explicit integration dependency. Setup/foundation deliberately avoid implementing business behavior before the first acceptance failure.

### Parallel opportunities and example for US1

T003 and T004 can run concurrently after T002: `.gitignore` and evidence documentation are disjoint. Shared pyproject.toml changes remain sequential.

Within US1, the production package is small and shared files overlap, so no story task is marked [P]. After T017, a limited parallel preparation example is drafting the independent `tests/adapters/test_identity_bridge.py` and `tests/adapters/test_graphql.py` assertions for T028/T030 in separate files. These drafts do **not** complete those tasks: their dependencies, executed behavioral Red and later Green remain in the stated order. Never parallelize writes to enroll.py/sqlite.py/bootstrap.py, share evidence files between workers or count a draft test as executed evidence. This is an execution option, not an instruction to spawn agents during task generation.

## Historical requirements and scenario traceability (T001–T050)

| Requirement / scenario | Owning tasks |
|---|---|
| FR-001; scenarios 13–14; verified identity independent of Student | T010–T012, T015–T019, T028–T029, T033 |
| FR-002, FR-007; scenarios 4–6 | T013–T014, T017, T020–T025, T033 |
| FR-003; shared course scenario 2, ineligible 7, changing facts 3 | T015–T016, T022–T027, T033–T035 |
| FR-004, SC-001; durable success scenario 1 | T010–T014, T023–T027, T030–T033 |
| FR-005, SC-003; duplicate 8, response loss 9, concurrency 10 | T015–T016, T022–T027, T036–T039 |
| FR-006, SC-002; all rejected attempts and unrelated concurrency 15 | T018–T023, T026–T027, T033, T036–T043 |
| FR-008; persistence failure scenario 11 | T026–T027, T040–T041 |
| FR-009, SC-004; exact precedence, combined failure scenario 12 | T018–T023, T030–T033, T038–T039, T043 |
| FR-010; prerequisite records unchanged | T024–T025, T033, T043 |
| Hexagonal / Full Bridge / quality / whole-function coverage | T005, T008–T009, T017, T024–T033, T044–T050 |
| Outside-In TDD evidence and final-state completion | T004, all US1 increments, T044–T050 |

## Historical implementation strategy (T001–T050)

1. Complete Setup and Foundational checks. Keep production free of business behavior until T010 acceptance Red.
2. Drive US1 outside-in: acceptance -> failing inner behavior -> minimum implementation -> refactor, repeating independently for each behavior. Core models precede orchestration implementation; adapters integrate afterward while acceptance guides the work.
3. Demonstrate the first durable eligible enrollment as an interim slice, then complete every specified rejection, race, retry and failure case. Do not call the interim success slice the completed MVP.
4. MVP is the **entire US1** plus mandatory final checks: one enrollment mutation, existing identity dependency, real SQLite and all fifteen acceptance examples. No UI, account/record management, capacity, terms, withdrawals or extra infrastructure.
5. Complete T048 quality execution/capture, then T049 manifest assembly, then T050 evidence validation and reviewer inspection on the final implementation state. A check result, an assembled manifest or a passing stage alone never implies completion. Task generation alone does not authorize deployment or claim any runtime check passed.



## Interrupted implementation: prior resume baseline (archival)

This section preserves the observations made when implementation resumed; it is archival,
not a statement of current completion status. Existing
uncommitted code, tests and evidence MUST be preserved and reviewed before resuming.
Only T051–T052 have been marked complete during this implementation attempt.

| Area | Observed state | Remaining owning tasks |
|---|---|---|
| Baseline and historical retention | `evidence/reconciliation/baseline.json` reports 66 focused tests passing; `history-index.json` and `evidence/history/pre-reconciliation/` preserve original artifacts | T051–T052 complete; later review still required |
| Lightweight tooling | Recorder/validator edits exist; retained tooling Green reports five tests passing; assembly still hardcodes historical `PAIRS` and the old review | T053–T055, T059–T060, T088 |
| Fitness simplification | Supplemental checks changed and Import Linter previously kept five contracts; equivalent negative protection and retained final evidence need audit | T056–T059 |
| Student details | Values, Student shape, host operation, schema, configured connections and seven test-function families exist; retained acceptance Green reports 21 passing cases | T061–T078 remain pending full verification |
| Focused regressions | Latest retained Student-details Green reports 117 focused acceptance/Domain/Application/SQLite tests passing | Not a full static, coverage, wheel, socket or final-quality pass |
| Failure-contract migration | Enrollment still catches constructor ValueError and raised UniqueConflict; identity adapter still catches broad Exception; row decoding still catches broad ValueError | T071, T079–T083 |

Retained command/result records are in `specs/001-enroll-course/evidence/reconciliation/`.
They include failed attempts and a syntax/collection failure; preserve every record,
but do not count setup/collection failures as behavioral Red. The later assertion
failures and passing executions need evidence-based review for coherent increments.
No intermediate snapshots, per-behavior approval or individual cycle inventory is
introduced by this review.

On resume, start with pending T053, audit existing edits against its criteria, and
finish the evidence/fitness foundation before proceeding further into story work.
Do not rerun historical tasks, regenerate scaffolding, overwrite working code, or
break already-correct behavior to manufacture Red. Add tests for genuine missing
behavior before implementing it; verify existing behavior and refactoring from Green.
Any observed execution-order or evidence gap must be reported honestly during T090–T094;
this task update cannot retroactively establish compliance.

The actual Domain record module is `src/enrollment/domain/models.py`; extend it rather
than create a competing `records.py`. Keep test module `tests/domain/test_records.py`.

## Phase 5: Reconciliation setup (shared)

**Purpose**: Establish the real baseline without reinitializing the project.

- [X] T051 Inspect current src/enrollment/, scripts/record.py, scripts/check_evidence.py, tests/architecture/test_quality_gates.py and this tasks.md working diff against the committed plan; run the focused baseline in specs/001-enroll-course/quickstart.md and retain actual results under specs/001-enroll-course/evidence/reconciliation/. Do not discard existing user edits or claim planned behavior is implemented.

- [X] T052 Inventory original specs/001-enroll-course/evidence/review.json and evidence/final/ artifacts with hashes in specs/001-enroll-course/evidence/reconciliation/history-index.json; preserve their bytes before any final output replacement, using a separate history archive if needed. Record T050 as pending reassessment, not automatically failed or passed under the amended rule.

## Phase 6: Shared evidence and architecture foundation

**Purpose**: Replace obsolete enforcement before relying on it for new work. T053–T055
and T056–T058 can proceed independently on disjoint files after T052; T059–T060 follow
both. Tests for changed gate behavior must run Red before implementation.

- [X] T053 In tests/architecture/test_quality_gates.py, execute meaningful failing tests for acceptance of consolidated cohesive-increment Red/Green commands/results without snapshots, hash chains, per-behavior maps/reviews or NO_REFACTOR artifacts; reject missing genuine behavioral Red, failed Green, environmental-only failure and stale final check evidence. Keep existing final-result integrity and coverage/scenario fixtures. Audit the retained tooling Red/Green records and current tests first; add meaningful missing tests for consolidated log ingestion, behavioral failure classification and final-result freshness. Do not repeat already-correct behavior merely to produce another Red.

- [X] T054 Implement the lightweight recorder in scripts/record.py driven by T053: retain actual commands, test identities, output/result references, exit results and sufficient chronological context, allowing consolidated evidence across coherent increments. Remove active snapshot/blob capture, global event-chain continuity, per-behavior mappings and mandatory refactor/approval stages that serve only superseded process rules; keep final digest utilities used by quality capture. Require only the recorder-specific T053 tests and relevant recorder regressions to pass at T054; validator-dependent T053 tests remain pending T055. Preserve recorder behavioral Red before its implementation and recorder Green afterward; preserve historical output.

- [X] T055 Align scripts/assemble_evidence.py and scripts/check_evidence.py with T053–T054: accept lightweight and referenceable historical evidence, remove fixed historical increment inventories and per-behavior protocol policing, retain final artifact hashes/digest freshness, actual check results and honest review decisions. Preserve validator behavioral Red before its implementation, adding focused tests before any uncovered change. At T055 require the complete T053 recorder/validator test suite and relevant regressions to pass Green; validate accepted consolidation and rejected missing/failed evidence without inventing a new mandatory approval format. Finish the still-legacy manifest assembly path: remove PAIRS as a mandatory completion inventory, ingest/reference actual reconciliation execution records and select the current separate review while preserving original review/history. Ensure lightweight records are hashed/referenced rather than left as unaudited manifest summaries; final validation must exercise this end-to-end path.

- [X] T056 Baseline allowed/violating dependency fixtures for tests/architecture/test_boundaries.py and pyproject.toml Import Linter contracts: retain inward direction, Domain/framework isolation, adapter independence and allowed HTTP-to-GraphQL/direct adapter-to-Domain usage. Demonstrate primary checker protection before deleting overlap; keep empty-scope detection and recursive module discovery. The supplemental boundary suite is already modified; demonstrate equivalent protection with controlled allowed/violating fixtures against the current primary checker instead of assuming the earlier edit proves equivalence.

- [X] T057 Consolidate duplicate general AST import rules in tests/architecture/test_boundaries.py after T056; make existing Import Linter contracts the primary graph verifier. Retain focused dynamic-loading, public annotation/method/nested type/alias/re-export checks for demonstrated gaps, with allowed and violating fixtures. Preserve converter/contract tests because static imports cannot prove semantic representation isolation. Audit nested annotations, methods, aliases and public re-exports in the current simplified suite; close actual gaps with targeted tests before further checker changes.

- [X] T058 Replace exact policy-call-name sets and source-substring/comparison bans in tests/architecture/test_boundaries.py with observable Domain ownership, policy delegation and first-match short-circuit tests in tests/application/test_enrollment_flow.py and tests/domain/test_policies.py before removing brittle assertions. Preserve meaningful protection and avoid a second general import-graph engine.

- [X] T059 Verify pyproject.toml, scripts/check_quality.py and scripts/check_evidence.py retain complete-Core branch=True/fail_under=100, unimported source discovery, no business suppressions and all static/contract gates. Extend meaningful gate fixtures in tests/architecture/test_quality_gates.py only where needed; explicitly report constitutional whole-function branch minimum separately from the unchanged stricter project target.

- [X] T060 Update specs/001-enroll-course/evidence/README.md and quickstart.md with the actual tested lightweight recording interface and final checks -> review -> assembly -> validation flow; run recorder/gate/architecture suites and retain foundation results in specs/001-enroll-course/evidence/reconciliation/. Keep historical files readable and unchanged.

## Phase 7: User Story 2 — Valid Student Details (P1)

**Goal**: Valid nonblank student details and globally unique whole-address caseless
email through the internal Python integration boundary; no management endpoint.

**Independent test**: Exercise all seven `student-details-1` through
`student-details-7` acceptance families with real temporary SQLite, durable reopened
state, rejected-change preservation and exactly one concurrent email claimant.

**Acceptance-first order**: T061 establishes relevant behavioral failure before shared
factory or Student behavior changes in T062 onward. Use inert importable shells only
when needed to reach assertions; import/signature errors do not count as Red.

- [X] T061 [US2] Create the inert host-integration acceptance harness and guiding tests in tests/acceptance/test_student_details.py and tests/support/database.py for seven stable scenario families and declared parameter variants; execute relevant observable behavioral Red before implementation. Preserve all existing enrollment scenarios and record failures honestly under specs/001-enroll-course/evidence/reconciliation/.

- [X] T062 [US2] Drive result-returning ID factories in src/enrollment/domain/values.py, outcomes.py and tests/domain/test_values.py from T061 and focused behavioral tests: preserve "Identifiers are nonempty opaque strings, compared exactly, with no trimming/case folding" and "runtime checks for actual string type and nonempty value". Return validation outcomes for raw input; guarded constructors remain internal misuse protection, not routine parsing. Factories already exist in values.py; verify result-returning invalid and valid paths, type distinctions and complete affected-function coverage rather than recreate them.

- [X] T063 [US2] (Amended 2026-10-22; amended criteria verified by T096–T100) Drive StudentName/StudentEmail values in src/enrollment/domain/values.py, outcomes.py and tests/domain/test_student_values.py: "Actual string containing a non-whitespace character; original text retained; no uniqueness" and "Same required-text invariant; whole supplied value casefold() is the comparison key". Apply FR-012 full Unicode case folding, including multi-character expansions, while retaining original spelling. Test None/non-text/empty/spaces/tabs/newlines/Unicode whitespace; verify composed café@example.com (U+00E9) and decomposed café@example.com (U+0065 U+0301) remain unequal with original spelling retained; no syntax/length/trimming/Unicode composition/provider normalization rules.

- [X] T064 [US2] (Amended 2026-10-22; amended criteria verified by T096–T100) Drive StudentEmail equality/hash in src/enrollment/domain/values.py and tests/domain/test_student_values.py: compare complete Unicode str.casefold() keys only between StudentEmail instances, equal values have equal hashes, heterogeneous __eq__ returns NotImplemented, original spelling survives. Cover the FR-012 conflict example Straße@example.com versus STRASSE@EXAMPLE.COM, casefold expansion, sets/dicts and significant spaces; do not assert unequal keys have unequal hashes. Equality/hash code already exists; add or verify direct value tests for symmetric equality/inequality, heterogeneous operands, Unicode expansion and set/dictionary behavior before declaring this task complete.

- [X] T065 [US2] Drive Student records/factories/replacement in src/enrollment/domain/models.py and tests/domain/test_records.py: "Student's frozen fields require both typed values, with no defaults"; enforce typed text on construction/reconstitution/change and preserve "One referenced programme; a dangling programme reference must remain representable so MISSING_PROGRAMME can be returned". Student identity/equality is StudentId alone; if hashable, hash only by immutable StudentId. Adapt affected Student constructors, test factories and repository doubles incrementally in tests/conftest.py, tests/support/database.py, tests/support/application.py and the owning tests alongside this model change, preserving approved assertions and intentional invalid fixtures. Reach genuine behavioral assertions before counting Red; constructor/import failures do not qualify. Verify the adapted focused regressions now rather than deferring them to T077. The Student shape already changed in models.py; audit constructor/reconstitution/replacement invariants, StudentId-only equality/hash and record factories, including complete affected-method coverage. Preserve current fixture adaptations.

- [X] T066 [US2] Drive email-availability policy in src/enrollment/domain/policies.py, outcomes.py and tests/domain/test_student_policies.py: absent/self owner permits saving, different StudentId rejects equal whole-address keys across all programmes; names need not be unique. Domain owns the predicate, Application supplies owner context without duplicating it.

- [X] T067 [US2] Define and test CREATE/REPLACE commands, returned results and separate owned student-record UoW in src/enrollment/application/student_contracts.py, ports.py and tests/application/test_student_details.py per contracts/student-details.md. Raw fields accept object/None; validate IDs then name then email; return explicit invalid-ID/text, existing-create, missing-replace, email-conflict and separate technical outcomes. Enrollment UoW gains no Student writes. Audit the partial StudentUnitOfWork contract for an explicit rollback capability and precise success/conflict outcomes: do not expose unrelated operation results from a save port. Align the existing dict command or replace it with a precise Core-owned command contract while preserving raw object/None input and all approved mode semantics.

- [X] T068 [US2] Drive create/full-replace orchestration in src/enrollment/application/student_details.py and tests/application/test_student_details.py: coordinate Domain factories and uniqueness policy, stop with no writes on rejection, use target identity for mode/self-exclusion, retain supplied programme without new existence checks, commit before Accepted. No business predicates duplicated and no constructor exception parsing.

- [X] T069 [US2] (Amended 2026-10-22; amended criteria verified by T096–T100) Drive registered connection functions and constrained storage in src/enrollment/adapters/persistence/sqlite.py, schema.sql and tests/adapters/test_sqlite.py: "name TEXT NOT NULL", "email TEXT NOT NULL", explicit text/nonblank checks and unique students_email_key expression index using Domain whole-address full Unicode casefold semantics from FR-012, including Straße@example.com conflicting with STRASSE@EXAMPLE.COM. Register deterministic functions before all schema access; invalid/null function results cannot bypass checks. Unconfigured writers fail closed; no NOCASE/lower/forged key fallback. Adapt affected named-column seeds, schema setup helpers and configured fixture connections in tests/support/database.py, tests/conftest.py and owning adapter tests alongside this schema change; preserve intentional legacy/corrupt fixtures. Schema setup failures are not behavioral Red; rerun affected tests against successfully configured production-schema fixtures before T077. Current SQL functions duplicate strip/casefold predicates in the adapter; drive delegation to public Domain validation/comparison mechanisms so storage and Domain cannot drift.

- [X] T070 [US2] Drive fresh/compatible initialization and legacy refusal in src/enrollment/adapters/persistence/sqlite.py and tests/adapters/test_sqlite.py: compatible repeated initialization preserves data, missing required fields fail clearly without schema alteration or invented defaults. No automatic migration/backfill. Update configured fixture connections only as needed for approved required fields. Adapt initialization-specific fixtures alongside the initialization change and verify their focused regressions here, not only at T077; setup failures alone do not count as behavioral Red.

- [X] T071 [US2] Drive Student reconstitution in src/enrollment/adapters/persistence/sqlite.py and tests/adapters/test_sqlite.py using Domain factory outcomes and both fields; invalid stored text or incompatible/corrupt schema becomes Core technical StorageFailure, never missing student/input rejection. Preserve original text/equality/StudentId identity and sanitize external diagnostics. Current _read catches ValueError around arbitrary conversion; use explicit factory outcomes for recognized invalid stored representations, while injected unrelated converter/programming errors propagate as unexpected faults.

- [X] T072 [US2] Drive the separate real student-record UoW in src/enrollment/adapters/persistence/sqlite.py and tests/adapters/test_student_uow.py: BEGIN IMMEDIATE before reads, target/email-owner reads, bound insert/full replace, explicit commit/rollback/close, precise Saved | EmailKeyConflict values. Only the email index violation becomes conflict; unrelated integrity errors remain technical; no INSERT OR REPLACE/IGNORE.

- [X] T073 [US2] Integrate the host operation with real configured SQLite in tests/acceptance/test_student_details.py and src/enrollment/application/student_details.py: acceptance 1–5/7, cross-programme/global conflicts, own-email case changes, original text, plus-tag/domain distinctions, complete replacements and preserved prior fields/enrollment rows on rejection. Execute relevant acceptance Red before uncovered integration behavior.

- [X] T074 [US2] Drive concurrent email claims and replacements in tests/acceptance/test_student_details.py and tests/adapters/test_student_uow.py, correcting only missing behavior in src/enrollment/adapters/persistence/sqlite.py: separate worker-owned connections, bounded synchronization, one committed winner, typed loser conflict and preserved old replacement state. No barriers after exclusive writer acquisition.

- [X] T075 [US2] Drive technical failure/cleanup classification in tests/application/test_student_details.py, tests/adapters/test_student_uow.py and src/enrollment/application/student_details.py: open/read/write/lock/commit/corruption faults become distinct StudentStorageFailure, programming/internal-contract errors propagate to host error handling, rollback/close cannot mask primary faults or compensate confirmed commits. Audit current finally-close behavior when both operation and cleanup fail; prove the primary error is preserved and cleanup diagnostics are recorded, without undoing confirmed commits.

- [X] T076 [US2] Exercise direct SQL constraints, function-registration failures, Unicode cases, corrupt/legacy refusal and compatible initialization in tests/adapters/test_student_uow.py and tests/adapters/test_sqlite.py using the production schema. Add focused corrections only after actual behavioral Red; verify invalid writes cannot bypass Domain-backed storage guarantees.

- [X] T077 [US2] Perform the final fixture compatibility and regression audit of tests/conftest.py, tests/support/database.py, tests/support/application.py and owning tests after incremental adaptation during T065/T069/T070 and any other affected model/schema change. Verify valid constructors, unique required Student details, named-column seeds, configured connections and doubles; preserve intentional corrupt/legacy fixtures and every approved assertion. Correct remaining fixture gaps and run affected regressions. This audit is not the first fixture adaptation; fixture-only changes require regression verification, not manufactured Red or constructor/import/schema setup failures.

- [X] T078 [US2] (Amended 2026-10-22; amended criteria verified by T096–T100) Run all seven named acceptance families and parameter variants in tests/acceptance/test_student_details.py plus focused Domain/Application/persistence tests; retain lightweight execution results under specs/001-enroll-course/evidence/reconciliation/. Confirm host-only access, explicit outcome contracts, StudentId identity and no added public endpoint; this checkpoint alone is not final completion. Current test functions are named test_student_details_1 through test_student_details_7; establish the contracted student-details-1 through student-details-7 identity mapping and declared parameter variants explicitly for T088. Passing function counts alone do not satisfy identity/variant completeness. The amended suite requires 23 named cases, including student-details-3[unicode-expansion] and student-details-4[unicode-composition], with reopened-state preservation assertions.

## Phase 8: User Story 1 — Enrollment compatibility and failure contracts (P1)

**Goal**: Preserve all enrollment outcomes with valid Student details and explicit
expected-failure contracts, including privacy, ordering, persistence and concurrency.

**Independent test**: All fifteen HTTP acceptance families using Flask `/graphql`,
real GraphQL, real SQLite and a deterministic verifier pass; reopen verifies state.
Invalid IDs, returned conflicts, provider outages and programming faults remain distinct.

- [X] T079 [US1] Run guiding HTTP/focused Red tests in tests/acceptance/test_enrollment.py, tests/application/test_identity.py and tests/application/test_enrollment_flow.py, then replace raw-ID exception parsing in src/enrollment/application/enroll.py with Domain factory outcome branches. Preserve verification -> target validation -> ownership -> course validation timing and exact FR-009 sequencing; negative verification/ownership must avoid persistence.

- [X] T080 [US1] Drive Added | PairConflict port values in src/enrollment/application/contracts.py, ports.py, enroll.py and tests/application/test_conflict.py: replace raised UniqueConflict, rollback/close before one fresh full ordered replay, retain higher-priority rejection precedence; a second conflict becomes technical StorageFailure/PERSISTENCE_FAILURE, not guessed duplicate.

- [X] T081 [US1] Drive precise enrollment-pair conflict translation in src/enrollment/adapters/persistence/sqlite.py, tests/adapters/test_transactions.py and tests/acceptance/test_enrollment.py: only pair-constraint conflict returns PairConflict; unrelated constraints/read/open/commit failures are technical. Preserve one committed enrollment, bounded retry, save-time eligibility and worker-owned connections.

- [X] T082 [US1] Drive provider negative/outage/programming distinctions in src/enrollment/adapters/identity/verifier.py, tests/adapters/test_identity_bridge.py and tests/application/test_identity.py: None means negative verification, documented operational faults mean IdentityUnavailable, invalid provider representation means technical boundary failure, programming/internal-contract faults propagate. Remove broad catches that fabricate outages; negative/outage paths access no persistence.

- [X] T083 [US1] Drive safe unexpected-error and cleanup propagation in src/enrollment/application/enroll.py, adapters/graphql/execution.py, adapters/http/app.py, adapters/persistence/sqlite.py and tests/application/test_enrollment_flow.py, tests/adapters/test_graphql.py: sanitize internal errors and record diagnostics, never fabricate business/outage results; cleanup preserves primary failures and confirmed commits.

- [X] T084 [US1] Prove Student restoration integrity through HTTP in tests/acceptance/test_student_record_integrity.py and tests/acceptance/test_enrollment.py: corrupt/legacy details cause sanitized PERSISTENCE_FAILURE, actual absence remains MISSING_STUDENT, no added FR-009 step and rejected enrollment cannot write Student or other prerequisite records. Drive any missing correction with relevant behavioral Red.

- [X] T085 [US1] Verify unchanged GraphQL schema/reasons and boundary conversion in tests/adapters/test_graphql.py and tests/adapters/test_http.py against contracts/schema.graphqls and src/enrollment/adapters/graphql/schema.graphqls: no new Student management fields/outcomes, no serialization-time database reads, exact privacy and precedence. Preserve direct-engine and HTTP contract tests.

- [X] T086 [US1] Validate required schema resources from a non-editably installed wheel in tests/adapters/test_package_resources.py and real Waitress socket/concurrency behavior in tests/adapters/test_server.py with valid Student details; verify checkout-independent origins, debug-disabled sanitized responses and deterministic cleanup. Retain actual results; correct only demonstrated gaps.

- [X] T087 [US1] Run all fifteen tests/acceptance/test_enrollment.py scenario families and focused identity/conflict/error/regression suites; verify FR-001–FR-010 and SC-001–SC-004, no exception-based expected control flow and no prerequisite mutation. Retain relevant results under specs/001-enroll-course/evidence/reconciliation/ without claiming T050 or final gates pass.

## Phase 9: Polish and cross-cutting completion

**Purpose**: Validate both stories, reassess historical process evidence under the
current rule, and enforce all approved final gates.

- [X] T088 (Amended 2026-10-22; amended criteria verified by T096–T100) Extend tests/architecture/test_quality_gates.py and scripts/assemble_evidence.py/check_evidence.py to require explicit identities for all 15 enrollment and seven Student-detail families plus declared variants in scripts/acceptance_inventory.py, including test_student_details_3[unicode-expansion] and test_student_details_4[unicode-composition] (23 required Student-detail cases); reject missing/ambiguous duplicate/skipped variants independently from TDD grouping. Retain consolidation-positive and missing-Red/failed-Green/stale-final negative tests; run failing behavioral gate tests before changes. Test actual assembled manifests containing current lightweight records and separate current review; do not rely solely on synthetic validator summaries or keep enrollment-only scenario completeness.

- [X] T089 Update README.md, specs/001-enroll-course/quickstart.md and evidence/README.md with tested host CREATE/REPLACE usage, required fields, casefold equality and StudentId identity, explicit failures, configured SQL functions, legacy refusal/external migration responsibility, actual lightweight evidence CLI and unchanged final gate sequence. Execute documented commands; add no management endpoint or migration workflow.

- [X] T090 Review the original specs/001-enroll-course/evidence/review.json and execution records under Constitution v2.0.0; record a separate evidence/reconciliation/review.json with concrete command/result references and coherent-increment reasoning. Grouping alone is not a violation; exclude environmental/import failures as Red, report genuine gaps and do not infer TDD from final Green. Never rewrite historical results or flip old review flags to fabricate resolution.

- [X] T091 Execute scripts/check-quality.sh on final source/config/tests after T088–T090: all acceptance/regression, socket, installed-wheel, contract/schema, fitness, Import Linter, strict mypy, Ruff and unchanged complete-Core 100% statement/branch gates. Preserve old final artifacts per T052 before replacement; retain actual raw output/digest under specs/001-enroll-course/evidence/final/checks/. Any later source/test/config edit requires recapture.

- [X] T092 Perform current completion review in specs/001-enroll-course/evidence/reconciliation/review.json against T091 results and retained new/historical execution evidence. Resolve or explicitly retain C1/T050 findings based on the current constitution and concrete evidence, not obsolete per-behavior criteria or new Green alone. Report all missing/failed/skipped/blocked mandatory checks and keep completion pending when warranted.

- [X] T093 Run scripts/assemble_evidence.py to write specs/001-enroll-course/evidence/final/manifest.json referencing actual final check results, exact acceptance identities/variants, consolidated/historical evidence, current review and source/config/test digest/artifact hashes. Preserve original historical manifests and include failures truthfully; assembly is not validation or a completion claim.

- [X] T094 Run scripts/check_evidence.py against specs/001-enroll-course/evidence/final/manifest.json and retain evidence/final/validation.json; require fresh consistent passing final gates, complete scenario identities and honest review/evidence. Reassess and complete historical T050 only when these requirements genuinely pass; otherwise leave T050/T094 pending with actual reasons. After relevant edits repeat T091–T094, including review. Never fabricate Red or waive approved gates.

## Dependencies and execution order

The following graph records the pre-amendment completed delivery sequence, followed by
the completed Phase 10 amendment verification chain.

```text
Historical T001–T049 retained; T050 completed through T090–T094 reassessment/final validation
T051 -> T052 -> (T053 -> T054 -> T055 || T056 -> T057 -> T058)
             -> T059 -> T060
T060 -> US2 T061 acceptance Red -> T062 -> T063 -> T064 -> T065 -> T066
     -> T067 -> T068 -> T069 -> T070 -> T071 -> T072 -> T073 -> T074
     -> T075 -> T076 -> T077 -> T078 (US2 independent checkpoint)
T078 -> US1 T079 -> T080 -> T081 -> T082 -> T083 -> T084 -> T085
     -> T086 -> T087 (US1 independent checkpoint)
T087 -> T088 -> T089 -> T090 historical reassessment -> T091 final checks
     -> T092 current review -> T093 assembly -> T094 validation / T050 decision
T094 + Unicode amendment edits -> T095 archive -> US2 T096 verification record
     -> T097 final checks -> T098 current review -> T099 assembly
     -> T100 validation / amendment completion decision
```

Phase 10 is strictly sequential: T097–T100 operate on one stable
src/tests/scripts/pyproject.toml/uv.lock state, and any edit to those paths after
T097 starts requires repeating T097–T100. T095 must finish before T097 because
quality capture and assembly overwrite the current final artifacts.

US2 runs first because valid Student values/schema support US1's equal-priority
compatibility work. It is independently tested without HTTP; US1 uses prepared valid
records without invoking the student-write operation. Shared values.py, enroll.py and
sqlite.py changes stay sequential. T061 precedes shared behavioral factory changes;
T053 precedes changed recorder/validator behavior. T054 passes the recorder-specific
subset; T055 passes the complete T053 suite. Fixtures adapt alongside their owning
model/schema changes; T077 is the final compatibility/regression audit. Existing correct behavior stays
Green; only genuinely missing behavior requires new Red.

## Parallel opportunities and examples

After T052, the T053–T055 evidence track and T056–T058 fitness track use disjoint
files; their internal tasks remain sequential. T059 and T060 wait for both. No new
whole-task [P] labels are used because conditional parallel tracks need this explicit
dependency context and later edits may touch shared modules.

US2 example: after T067, independent test-only drafting for
`tests/adapters/test_student_uow.py` and `tests/acceptance/test_student_details.py`
may proceed on separate files. Execute the owning cohesive increments in the stated
order; a draft is not execution evidence or completion. Do not parallelize sqlite.py.

US1 example: after T083, independent contract-test drafting in
`tests/adapters/test_graphql.py` and package-resource test preparation in
`tests/adapters/test_package_resources.py` may proceed separately. T084–T087 still
respect prerequisites and serialize shared fixture/adapter changes. Evidence capture
and final review operate on one stable source state.

## Requirements traceability

| Basis | Completed owning tasks |
|---|---|
| FR-011 / SC-005; US2 1–2, required text/restoration | T061–T065, T067–T072, T075–T078 |
| FR-012 / SC-006; US2 3–6, global/caseless/concurrent uniqueness | T064, T066–T074, T076–T078 |
| FR-013 / SC-007; US2 2,3,6,7, explicit rejection and preservation | T067–T068, T071–T078 |
| StudentEmail equality/hash and StudentId entity identity | T064–T066, T070, T072, T078 |
| FR-001–FR-010 / SC-001–SC-004, all 15 US1 scenarios | T079–T087 plus historical implementation |
| Domain-owned factories / explicit expected outcomes / technical errors | T062–T068, T070–T075, T079–T084 |
| Architecture simplification without lost isolation/conversion protection | T056–T059, T085, T091 |
| Cohesive TDD / consolidated lightweight evidence / history preservation | T051–T055, T060, each behavioral task, T088–T094 |
| Constitutional coverage floor versus unchanged approved target | T059, T088, T091–T094 |
| FR-012 / SC-006 Unicode amendment; US2 3[unicode-expansion], 4[unicode-composition]; 23-case inventory | T095–T100 |

## Implementation strategy and MVP

1. Reconcile current edits and preserve original evidence before replacing outputs.
2. Migrate obsolete process enforcement and consolidate fitness checks with equivalent
   protection; validate evidence-tool behavior before relying on it for new increments.
3. Complete US2 through its host boundary, then US1 failure-contract and compatibility
   work through HTTP. Use cohesive increments guided by acceptance outcomes, not an
   exhaustive cycle inventory.
4. The original US1-only MVP remains the historical baseline. For this extension, the
   reviewable MVP includes required Student details plus preserved US1 behavior and
   mandatory final gates. A first valid save is an interim demonstration, not completion.
5. Reassess C1/T050 under v2.0.0 with real evidence, run final checks, review, assemble
   and validate. Grouping is permitted; missing genuine Red/Green remains reportable.
   Planning/task generation does not approve implementation or certify compliance.
6. For the Unicode acceptance amendment, verify the unchanged production behavior
   against the 23-case suite and refresh final evidence through T095–T100. No
   production change is planned; a genuine failure is handled as new behavioral work
   under T096.

No dependency upgrade, new public management endpoint, authentication flow, email
syntax/normalization rule or automatic data migration is included.

## Historical final implementation outcome (before Unicode acceptance amendment)

All T001–T094 tasks were completed for the pre-amendment suite. T090–T094
completed the T050 reassessment and closed C1 under Constitution v2.0.0 based on the
retained execution evidence and passing final validation. The original failed review
and execution records remain unchanged;
`evidence/reconciliation/review.json` records the separate current decision under
Constitution v2.0.0. Historical per-behavior descriptions remain archival.

Final quality capture passed 207 tests, all five Import Linter contracts, strict mypy,
Ruff lint/format, installed-wheel resources, real Waitress sockets, schema/contracts
and complete Core 100% statement-and-branch coverage. All 15 enrollment families and
seven Student-detail families with the then-required 21 parameterized cases were verified.
The amended suite requires 23 cases; this historical capture does not verify the amendment.
The final manifest references actual consolidated/historical execution records and
current review; `evidence/final/validation.json` reports a passing result for the final
source/config/test digest. Passing coverage alone was not used as proof of TDD.

The 21 archived original review/final artifacts retain their indexed hashes. New
execution records preserve failed attempts and environmental/setup failures without
counting those failures as behavioral Red. No historical result was rewritten and no
correct behavior was broken to manufacture Red. Future source/test/config changes
require final quality recapture, review, assembly and validation.

## Phase 10: Unicode acceptance amendment — final verification

**Purpose**: Re-establish passing final evidence after the 2026-10-22 refinement of
FR-012, US2 scenarios 3–4 and SC-006. Constitution V forbids a completion claim until
T100 passes.

**Current status**: US2 scenario 3 now includes `unicode-expansion`
(`Straße@example.com` conflicts with `STRASSE@EXAMPLE.COM`); scenario 4 includes
`unicode-composition` (precomposed `café@example.com` and decomposed
`cafe\u0301@example.com` are both accepted and retained). tests/domain/test_student_values.py
adds `test_email_composition_is_not_normalized`, and scripts/acceptance_inventory.py
now requires 23 Student-detail cases. These edits changed tests/ and scripts/, which
the evidence digest in scripts/record.py covers, so evidence/final/checks/,
evidence/final/manifest.json, evidence/final/validation.json and
evidence/reconciliation/review.json all describe a stale digest. T063, T064, T069,
T078 and T088 keep their historical completed markers; their amended criteria are
verified only by T096–T100. No production source change was made: the amendment
makes existing casefold behavior explicit, so no new behavioral Red was expected or
manufactured.

**Outcome (2026-10-22)**: T095 archived the pre-amendment manifest, validation,
tests.xml, coverage.json and review byte-for-byte under
evidence/history/pre-unicode-amendment/ with a verified hash index. T096's
verification record
(evidence/reconciliation/1792685275374012602-unicode-amendment-verification.json)
passed 38 tests on its first run, including all 23 Student-detail cases, so no Red
was recorded. T097 passed all eight checks on digest
`c0dbcd8d151a61d8e71f2d7229c17b38b54fc56d7e19e808e305a51ce8aa9faa`: 210 tests with
none skipped (including installed-wheel and real Waitress socket tests), 15
enrollment scenarios, 23 Student-detail cases with scenario properties, 5 Import
Linter contracts kept, strict mypy, Ruff lint/format and 100% Core statement and
branch coverage (305 statements, 80 branches). T098 recorded the current review
(`passed: true`). T099 assembled a manifest hashing 121 artifacts, and T100's
evidence/final/validation.json reports `passed: true` with no errors for the same
digest. Any later edit to src/, tests/, scripts/, pyproject.toml or uv.lock
requires repeating T097–T100.

**Independent test**: The 23 named `tests/acceptance/test_student_details.py` cases,
including `test_student_details_3[unicode-expansion]` and
`test_student_details_4[unicode-composition]`, pass with `scenario` properties
`student-details-3` and `student-details-4` in evidence/final/checks/tests.xml;
`.venv/bin/python -m scripts.check_evidence` then reports `"passed": true` for the
current digest.

- [X] T095 Archive the current pre-amendment final evidence before anything overwrites it: copy specs/001-enroll-course/evidence/final/manifest.json, final/validation.json, final/checks/tests.xml, final/checks/coverage.json and reconciliation/review.json byte-for-byte into specs/001-enroll-course/evidence/history/pre-unicode-amendment/ at the same relative paths (final/..., reconciliation/review.json). Write specs/001-enroll-course/evidence/history/pre-unicode-amendment/index.json mapping each archived relative path to its SHA-256, and verify each hash against its source before continuing. Do not modify reconciliation/history-index.json, history/pre-reconciliation/ or history/pre-student-details/. final/checks/*.json need no manual copy because scripts/check_quality.py archives them into final/checks/history/ automatically.

- [X] T096 [US2] Record a verification-stage run of the amended suites with `.venv/bin/python -m scripts.record unicode-amendment verification .venv/bin/pytest -v -p no:cacheprovider tests/acceptance/test_student_details.py tests/domain/test_student_values.py`, producing specs/001-enroll-course/evidence/reconciliation/<ns>-unicode-amendment-verification.json. Confirm exit code 0, 23 passing `test_student_details_*` cases including `[unicode-expansion]` and `[unicode-composition]`, and a passing `test_email_composition_is_not_normalized`. Use stage `verification`, not `red`: production behavior is unchanged, and a passing first run is the expected honest outcome. If either new case genuinely fails, stop. Keep the verification record as context, then rerun the same command as `.venv/bin/python -m scripts.record unicode-amendment red ...`, because scripts/check_evidence.py counts only red-stage records with exit code 1 and an AssertionError as Red and scripts/assemble_evidence.py ignores verification records. Correct only the demonstrated defect in src/enrollment/domain/values.py or src/enrollment/adapters/persistence/sqlite.py, record the Green with `scripts.record unicode-amendment green ...`, and only then continue.

- [X] T097 Run `bash scripts/check-quality.sh` on the stable amended state after T095–T096, with no further edits to src/, tests/, scripts/, pyproject.toml or uv.lock. Require all eight checks in specs/001-enroll-course/evidence/final/checks/ (tests, architecture, imports, typing, lint, format, coverage-report, coverage-data) to exit 0 with `digest == digest_after`. Confirm tests.xml contains all 15 `test_scenario[N-...]` enrollment cases and all 23 STUDENT_CASES names with matching `scenario` properties, and that coverage.json reports complete Domain/Application 100% statement and branch coverage. Preserve any failed result, fix it through the owning task, then rerun T097.

- [X] T098 Update specs/001-enroll-course/evidence/reconciliation/review.json as the current completion review against T097: set `source_digest` to the T097 digest and refresh `final_checks` with each check's reference, exit code and digest. Add a `new_execution_records["unicode-amendment"]` entry for the T096 record and a `new_work_review` entry explaining verification-only treatment of the clarified FR-012 behavior (no new Red claimed, no TDD inferred from Green). Append the T096 record and every history/pre-unicode-amendment/ file to `historical_records` so that assembly hashes them. Keep `historical_reassessment`, earlier entries and the "21 initial acceptance variants" statement unchanged as historical facts. Set `passed` to true only if T097 fully passed and the review finds no gap; otherwise set it to false and record the reasons in `notes`.

- [X] T099 Run `.venv/bin/python -m scripts.assemble_evidence` to rewrite specs/001-enroll-course/evidence/final/manifest.json. Confirm its `digest` equals the T097 digest, `review` equals the T098 file, and `artifacts` hashes the eight check files, tests.xml, coverage.json, review.json, the T096 record and the archived pre-unicode-amendment files. Assembly is not validation or a completion claim.

- [X] T100 Run `.venv/bin/python -m scripts.check_evidence` and retain specs/001-enroll-course/evidence/final/validation.json. Mark T095–T100 complete only if it reports `"passed": true` with no errors and a digest equal to T097's. Then update this Phase 10 status paragraph and the outcome sections above with the actual test totals and the 23-case result. If validation fails, leave the failing tasks unchecked, record the reported errors here, and repeat from the earliest affected task; any later edit to src/, tests/, scripts/, pyproject.toml or uv.lock requires repeating T097–T100.
