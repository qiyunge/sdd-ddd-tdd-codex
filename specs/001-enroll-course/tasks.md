# Tasks: Student Self-Enrollment

**Input**: Design documents in `specs/001-enroll-course/`.
**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contract](contracts/enrollment-api.md), [SDL](contracts/schema.graphqls), [quickstart.md](quickstart.md), [student-details contract](contracts/student-details.md); Constitution v1.3.0.
**Tests**: Mandatory Outside-In TDD under the constitution and the user's prior instructions. Implementation status is tracked by the checked task markers below.
**Organization**: Two P1 stories: US1 (Student Self-Enrollment) and US2 (Valid Student Details). T001–T050 retain the historical delivery record; new extension work is T051–T087 in Phases 5–9. Paths below are repository-relative. Checked historical tasks do not establish extension completion.

## Format and execution rules

Tasks use `- [ ] Tnnn [P?] [USn?] description with paths`. [P] means independent files/work after stated prerequisites, not permission to bypass test-first ordering. Story tasks carry [US1] or [US2]; shared/final tasks do not.

HTTP acceptance tests establish and guide externally observable behavior. Execute an acceptance assertion Red when that behavior is not yet implemented. If it is already Green, preserve it, record that observation and use a genuinely failing focused inner test to drive the next unimplemented behavior. Every independently testable business/adapter increment still follows executed Red -> Green -> Refactor; a prior green acceptance assertion does not waive its focused behavioral Red. Each Green task below is a sequence of small Red/Green/Refactor cycles, **not** permission to implement its entire paragraph after one failing test. Keep guiding acceptance assertions active and rerun them as each slice evolves. An import error, missing dependency, invalid configuration or unrelated failure is not behavioral Red. Introduce only inert importable interfaces/harness shells as necessary to reach the assertion, then execute the intended failure before production behavior. Never weaken tests, manufacture failures, introduce temporary bypasses or change correct production behavior to force Red.

For each increment retain commands, stdout/stderr, exit codes, execution order, test IDs and source revision/diff digest under `specs/001-enroll-course/evidence/<task-id>/`. Record no-refactor rationale when applicable and rerun relevant tests. Do not mark an implementation task done until its focused checks pass and evidence exists. Final checks must match the final source/config/test digest; evidence/build output is excluded from that digest to avoid self-reference.

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

- [ ] T050 Execute scripts/check_evidence.py against specs/001-enroll-course/evidence/final/manifest.json after T049: validate completeness, cross-reference consistency, actual check results, required scenarios, increment evidence and digest freshness against the current source/config/tests. Fail closed on missing/failed/skipped/blocked mandatory checks, inconsistent references or stale state. Retain the validation result in specs/001-enroll-course/evidence/final/validation.json; reviewer inspects raw TDD transcripts. Any source/test/config edit requires repeating T048 -> T049 -> T050; declare feature completion only after all three stages and the review pass.


## Historical execution outcome (T001–T050)

The functional implementation and final quality capture pass: 148 tests, all fifteen numbered acceptance scenarios, 100% complete Core statement/branch coverage, strict mypy, Ruff and five Import Linter contracts. T048 captured raw results and T049 assembled the matching manifest.

**T050 remains incomplete.** Evidence validation was executed and failed closed solely because the review did not pass. Several early increments used grouped Red suites followed by grouped implementations, so the recorded history does not fully demonstrate the required per-behavior Red–Green–Refactor execution order. Checked delivery markers above do not resolve that process nonconformance or imply feature completion. See [review](evidence/review.json) and [final validation](evidence/final/validation.json). No historical result was rewritten or manufactured to claim compliance.

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


## Student details extension — execution baseline

**Status**: All new tasks are unstarted. T050 remains pending; no historical task marker or evidence transcript has been changed by this update. The original grouped-TDD review failure is still a completion blocker. New evidence cannot reconstruct missing historical ordering or authorize a constitutional waiver.

**Input**: Updated spec FR-011–FR-013, SC-005–SC-007 and User Story 2 scenarios 1–7, plus plan extension and contracts/student-details.md. Existing Python 3.12, uv.lock, graphql-core, Flask, Waitress, SQLite and quality tooling are retained. No dependencies, public management endpoint, email syntax rules, login behavior or data migration are added.

**Execution rule for every new behavioral task**: Select and execute its guiding acceptance assertion, write/execute a focused test that fails for the expected observable reason, implement only that independently testable behavior, rerun Green, then refactor/rerun or record a no-refactor rationale. Repeat this sequence within a task for each distinct behavior; a grouped Red followed by a grouped implementation is insufficient. Use `scripts/record.py` with fresh task IDs and distinct sub-increment directories under `specs/001-enroll-course/evidence/` where a task includes multiple cycles. Preserve raw output, command, exit status, test identity, revision and diff association in order. Import errors, constructor arity failures and inert-shell exceptions are not behavioral Red. Do not disable existing correct behavior to manufacture Red. Pure fixture/documentation changes justified by required fields need regression verification, not artificial failures.

## Phase 5: Extension setup (shared infrastructure)

**Purpose**: Establish the current baseline and fresh evidence scheme without reinitializing the project.

- [ ] T051 Inspect pyproject.toml, uv.lock, specs/001-enroll-course/evidence/review.json and specs/001-enroll-course/evidence/final/validation.json; run the existing focused baseline from quickstart.md and record actual results/source association in specs/001-enroll-course/evidence/T051/. Before any later capture replaces final artifacts, archive the existing evidence/final/ files and review.json with their original hashes under specs/001-enroll-course/evidence/history/pre-student-details/. Preserve T050's unresolved historical process failure and all existing transcripts; no upgrade, reset or fabricated pass.
- [ ] T052 Document the extension increment registry and per-behavior capture procedure in specs/001-enroll-course/evidence/README.md: separate new text/model/policy/integration/schema/restore/race/gate increments from historical evidence, map all T054–T082 behavioral cycles, retain their ordered Red/Green/Refactor references, and require all 15 enrollment plus 7 student-detail scenario families with explicit parameter variants. Explain that old review failure cannot be overwritten by fresh green results.

**Checkpoint**: Historical baseline is recorded truthfully and new evidence has unique identities.

## Phase 6: Extension foundation (blocking prerequisites)

**Purpose**: Enable executable acceptance at the declared host Python boundary without implementing business behavior.

- [ ] T053 Prepare isolated fixture plumbing in tests/support/student_details.py and tests/acceptance/test_student_details.py for the host integration boundary, independent temporary files, production-schema initialization, configured worker-owned connections, snapshots and reopen checks. Add only the inert importable command/result/operation declarations needed in src/enrollment/application/student_details.py and src/enrollment/application/student_contracts.py to reach behavioral assertions; no validation, uniqueness policy, SQL write, fabricated Accepted result or new web route. Do not count a missing symbol, NotImplementedError or import failure as the first behavioral Red.

**Checkpoint**: A test can invoke the real intended Python boundary and assert its result/state. Valid fixtures must eventually use the production schema; deliberately incompatible/corrupt schemas remain explicit special fixtures.

## Phase 7: User Story 2 — Valid Student Details (P1)

**Goal**: Establish, restore and fully replace Student details with required nonblank text and globally unique whole-address caseless email, preserving old state on rejection.

**Independent test**: Invoke the internal Application operation with real file-backed SQLite, without HTTP or an identity provider; exercise stable `student-details-1` through `student-details-7` families and reopen records. Two concurrent different students claiming one address produce one committed winner and one distinguishable conflict. Direct Domain/reconstitution and SQL tests complement these acceptance outcomes.

**Ordering**: US1 and US2 have equal priority. US2's record/schema work precedes US1 extension regression because enrollment consumes Student. Existing US1 functionality remains the baseline; the extension does not require rebuilding it.

### Acceptance first, then Domain invariants

- [ ] T054 [US2] Define the seven contract acceptance families in tests/acceptance/test_student_details.py with explicit parameter IDs from specs/001-enroll-course/contracts/student-details.md: retained valid details; missing/empty/whitespace/non-text rejection; exact/local/domain/mixed-case cross-programme conflict; distinct whole addresses; self/case-only replacement; concurrent claim; valid/conflicting replacement. Execute scenario 1's result/durability assertion Red before business edits; activate and execute each later guiding assertion before its behavior slice, keeping failures attributable to business behavior rather than unavailable imports or schema setup.
- [ ] T055 [US2] Drive StudentName and its typed invalid-name reason in tests/domain/test_student_values.py and src/enrollment/domain/values.py plus src/enrollment/domain/outcomes.py. Quote the data-model constraint "Actual string containing a non-whitespace character; original text retained; no uniqueness". Execute separate Red/Green/Refactor cycles for valid retained text, empty/missing/non-text, spaces/tabs/newlines and non-ASCII whitespace including NBSP; reject invalid construction and never trim retained text.
- [ ] T056 [US2] Drive StudentEmail and invalid-email reason in tests/domain/test_student_values.py, src/enrollment/domain/values.py and src/enrollment/domain/outcomes.py. Quote "Same required-text invariant; whole supplied value casefold() is the comparison key". Preserve supplied spelling, validate actual text/nonblank, compare the complete local part plus domain with Python 3.12 casefold including Straße/STRASSE; surrounding whitespace remains significant. No syntax, length, provider alias, plus-tag/dot or composition-normalization rule; keep separate per-behavior cycles.
- [ ] T057 [US2] Drive the extended frozen Student in tests/domain/test_records.py and src/enrollment/domain/models.py: quote "Student's frozen fields require both typed values, with no defaults" and "Construction, reconstitution and validated replacement enforce types and text invariants regardless of caller". Add required name: StudentName/email: StudentEmail, reject wrong typed values via behavioral assertions rather than missing-argument errors, retain "One referenced programme; a dangling programme reference must remain representable so MISSING_PROGRAMME can be returned", and adapt existing Domain fixtures only as required by the approved constructor change.
- [ ] T058 [US2] Drive the pure email-availability policy and EmailConflict reason in tests/domain/test_student_policies.py, src/enrollment/domain/policies.py and src/enrollment/domain/outcomes.py: candidate StudentId plus absent owner permits assignment; same owner permits unchanged/case-only email; different owner rejects regardless of programme. Supply contextual facts from callers; no Domain repository dependency or Application duplicate predicate. Capture each policy branch's Red before its implementation.

### Application integration through separate owned ports

- [ ] T059 [US2] Complete the neutral CREATE/REPLACE command, typed result union and separate student-record UoW/factory Protocol declarations in src/enrollment/application/student_contracts.py and src/enrollment/application/ports.py, with contract assertions in tests/application/test_student_details.py. Raw name/email fields accept object/None as invalid input without unchecked Any; operation mode is explicit, full replacement includes both IDs and both detail values, and results distinguish Accepted, InvalidStudentDetails(field), InvalidIdentifier, EmailConflict, StudentAlreadyExists, StudentNotFound and StorageFailure. Keep student-write methods absent from the enrollment UoW and Domain free of Application imports.
- [ ] T060 [US2] Drive the first valid CREATE flow in tests/application/test_student_details.py and src/enrollment/application/student_details.py using port doubles: construct valid Domain candidate, open the separate UoW, load target then global email owner, delegate Domain availability, insert once and commit before Accepted, materialize output without lazy reads and close the session. Branchless orchestration also requires behavioral tests; add only the path driven by the executed acceptance/inner failures.
- [ ] T061 [US2] Drive invalid-input short circuits in tests/application/test_student_details.py and src/enrollment/application/student_details.py with separate cycles for invalid IDs, missing/non-text/blank name, missing/non-text/blank email and both-invalid name-first precedence. Return typed field-specific errors without echoing names/emails, constructing invalid Domain state, opening persistence or altering records. Keep Domain as the validation owner; Application only catches/propagates typed results.
- [ ] T062 [US2] Drive CREATE-existing-ID, REPLACE-missing-ID and full valid REPLACE in tests/application/test_student_details.py and src/enrollment/application/student_details.py. Check target existence before email owner lookup; never mistake these operation results for EmailConflict. Use the explicitly supplied programme without requiring its existence, keep Student immutable via a validated replacement candidate, and preserve other Student/enrollment records.
- [ ] T063 [US2] Drive Application propagation of absent/self/different email-owner Domain outcomes in tests/application/test_student_details.py and src/enrollment/application/student_details.py. Reject a different owner without writing/committing, allow self ownership including case-only updates, and preserve prior fields on rejection. Load the owner globally without programme filtering; Application sequences the policy but never repeats its equality/business predicate.

### Persistence, constraints and reconstitution

- [ ] T064 [US2] Drive a shared configured-connection helper in tests/adapters/test_student_sqlite.py and src/enrollment/adapters/persistence/sqlite.py: register deterministic required-text and whole-email-key SQL functions that delegate to public Domain mechanisms on initialization/enrollment/student-integration connections. Handle invalid/null/non-text input safely so CHECK cannot pass by returning NULL. Keep connection ownership in its creating thread, no global connection, no ASCII NOCASE/lower fallback and no business logic duplicated in adapters.
- [ ] T065 [US2] Drive the production students schema in tests/adapters/test_student_sqlite.py and src/enrollment/adapters/persistence/schema.sql. Quote "name TEXT NOT NULL", "email TEXT NOT NULL", "Add typeof/text/nonblank checks to the students table" and "unique expression index students_email_key on the registered Domain-backed email comparison function, across all students without programme in the key". Retain original email text; derive the key inside the expression index so no writable forged key can bypass it. Preserve every existing key/reference and dangling-programme behavior; add no default/backfill or new record type.
- [ ] T066 [US2] Drive initialization compatibility in tests/adapters/test_student_sqlite.py and src/enrollment/adapters/persistence/sqlite.py: fresh schema initializes, compatible repeat initialization preserves records/indexes, and legacy students without required columns is detected before any destructive/schema change and refused clearly. Existing incompatible data is not fabricated, migrated or silently accepted. Test raw legacy data/schema unchanged after refusal and sanitize runtime failure separately from host setup diagnostics.
- [ ] T067 [US2] Drive Session.student reconstitution in tests/adapters/test_student_sqlite.py and src/enrollment/adapters/persistence/sqlite.py: select both added fields, call validating StudentName/StudentEmail/Student constructors, return None only for true absence, and translate malformed/blank/non-text stored details to Core StorageFailure. Preserve originally supplied spelling/whitespace, opaque IDs and dangling programme references. Use explicit corruption fixtures; do not weaken production constraints.
- [ ] T068 [US2] Drive the separate student-record UoW implementation in tests/adapters/test_student_sqlite.py, tests/adapters/test_transactions.py and src/enrollment/adapters/persistence/sqlite.py: BEGIN IMMEDIATE before target/global-key lookup, validating reads, bound-column INSERT/full-field UPDATE without replacing identity/deleting the row, explicit SQL COMMIT/ROLLBACK with autocommit=True and worker-local close. Implement only student-record ports; enrollment Session must retain Enrollment-only writes. Test fresh-connection visibility and unchanged enrollments/other students.
- [ ] T069 [US2] Drive specific email-index conflict translation in tests/adapters/test_student_sqlite.py and src/enrollment/adapters/persistence/sqlite.py, with Core failure representation in src/enrollment/application/student_contracts.py as needed. Translate only students_email_key's unique violation to the dedicated email conflict; distinguish duplicate StudentId, enrollment-pair uniqueness, required-text/check and other SQL integrity errors. Never use INSERT OR REPLACE/IGNORE, blanket IntegrityError mapping or leak raw SQL/exception detail through Core.
- [ ] T070 [US2] Connect the actual Application operation to the separate SQLite factory using tests/support/student_details.py and only the required composition in src/enrollment/bootstrap.py; keep it a host-callable Python capability. Turn scenario families 1–5 and 7 Green in tests/acceptance/test_student_details.py and exercise actual repository restoration; use sub-increment Red/Green/Refactor for any remaining production gap. Prove plus tags/different domains remain distinct, repeated names are permitted, full spelling is retained and rejected creation/change preserves snapshots. Add no Flask/GraphQL route.

### Concurrent claims and failure guarantees

- [ ] T071 [US2] Execute family 6's guiding Red or truthful already-green observation, then drive any missing concurrent-claim behavior in tests/acceptance/test_student_details.py, tests/adapters/test_student_sqlite.py and src/enrollment/adapters/persistence/sqlite.py. Use two independent worker connections and bounded events proving overlapping exact/case-varied claims across programmes: one committed Accepted, one EmailConflict, zero duplicates. Never place a two-worker barrier after the single-writer lock or count an environmental lock/setup failure as behavioral Red.
- [ ] T072 [US2] Extend concurrent-claim coverage in tests/acceptance/test_student_details.py and tests/adapters/test_student_sqlite.py to a losing REPLACE and Unicode caseless collisions, including Straße@example.com versus STRASSE@EXAMPLE.COM. Capture any missing behavior's Red before changes in src/enrollment/application/student_details.py or src/enrollment/adapters/persistence/sqlite.py; verify every old field/enrollment survives a rejected change and same-student case-only replacement remains valid. Preserve already-correct behavior without manufacturing Red.
- [ ] T073 [US2] Drive student-record failure lifecycle in tests/application/test_student_details.py, tests/adapters/test_student_sqlite.py and src/enrollment/application/student_details.py plus src/enrollment/adapters/persistence/sqlite.py: open/lock/read/insert/update/pre-commit failure, rollback/close, confirmed commit response loss and ambiguous commit. Return sanitized StorageFailure instead of false success; no partial pre-commit record or destructive compensation after confirmed/possible commit. Record one expected-failure/minimum-change cycle per uncovered behavior.
- [ ] T074 [US2] Drive direct-write enforcement and registration failure in tests/adapters/test_student_sqlite.py against src/enrollment/adapters/persistence/schema.sql and src/enrollment/adapters/persistence/sqlite.py: configured raw inserts/updates cannot store blank text or exact/ASCII/Unicode caseless duplicates or forge a key; unconfigured connections fail closed without weaker comparison. Check missing attributes/NULL and significant whitespace with production schema and no programme key component; make only test-driven corrections and rerun acceptance.
- [ ] T075 [US2] Execute all seven student-detail scenario families and focused new Domain/Application/adapter tests from tests/acceptance/test_student_details.py, tests/domain/test_student_values.py, tests/domain/test_student_policies.py, tests/application/test_student_details.py and tests/adapters/test_student_sqlite.py; inspect fresh-connection snapshots for create, restoration, replacement, conflict and concurrency. Retain actual output in specs/001-enroll-course/evidence/T075/; no skipped variants or unverified constructor-only claim of global uniqueness.

**Checkpoint**: US2 is independently testable through the host boundary, all seven families pass, and new behavioral cycles have reviewable evidence. This does not resolve T050 or establish final completion.

## Phase 8: User Story 1 — Student Self-Enrollment with extended Student (P1)

**Goal**: Preserve the entire enrollment contract while reading the new valid Student shape.

**Independent test**: Run all fifteen numbered enrollment scenarios through Flask POST /graphql with valid required details in real SQLite; verify unchanged first-match results, durable enrollments, no student mutation and sanitized corrupt-record failure.

- [ ] T076 [US1] Update existing Student factories/repository doubles and direct SQL seeds in tests/support/database.py, tests/support/application.py, tests/conftest.py, tests/application/test_enrollment_flow.py, tests/application/test_conflict.py, tests/application/test_identity.py, tests/application/test_prerequisites.py and other callers found with rg in tests/ to supply valid unique required name/email. Replace the weaker valid-fixture schema with configured production schema initialization and named-column inserts; isolate intentional corrupt/legacy fixtures. Preserve business assertions and use the approved field contract to justify fixture changes; do not skip old tests or add constructor defaults.
- [ ] T077 [US1] Run all fifteen stable scenarios in tests/acceptance/test_enrollment.py and the existing race/retry/concurrency/fault suites, then add corruption/reconstitution HTTP acceptance in tests/acceptance/test_student_record_integrity.py: malformed stored Student details yield sanitized PERSISTENCE_FAILURE, true absence still MISSING_STUDENT, negative verification/ownership still avoids storage, and no new business step changes FR-009. Drive any newly uncovered correction in src/enrollment/adapters/persistence/sqlite.py and src/enrollment/application/enroll.py with fresh expected behavioral Red; retain existing student/programme/course/offer snapshots.
- [ ] T078 [US1] Verify the unchanged SDL and result enums in tests/adapters/test_graphql.py and tests/adapters/test_http.py against specs/001-enroll-course/contracts/schema.graphqls and src/enrollment/adapters/graphql/schema.graphqls: enrollment still accepts only its existing fields, discloses no detail-conflict result and cannot create/update Student. Preserve exact FR-009 precedence and no lazy database reads during serialization; add tests before any needed adapter correction in src/enrollment/adapters/graphql/execution.py or src/enrollment/adapters/http/app.py.
- [ ] T079 [US1] Validate the extended production schema from a built, non-editably installed wheel in tests/adapters/test_package_resources.py, then rerun real Waitress socket/concurrency checks in tests/adapters/test_server.py with valid student details. Preserve checkout-independent resource origins, debug-disabled sanitized responses and worker-owned connections; correct packaging/fixture issues only when demonstrated, retaining results in specs/001-enroll-course/evidence/T079/.

**Checkpoint**: US1 remains independently functional through HTTP with the new Student shape. All fifteen enrollment scenarios and seven student-detail families are now required for combined completion.

## Phase 9: Extension polish and cross-cutting completion gates

**Purpose**: Enforce architecture, complete Core coverage and honest final-state evidence across both stories.

- [ ] T080 [P] Drive any missing discovery/signature/ownership fitness checks in tests/architecture/test_boundaries.py for src/enrollment/application/student_details.py, src/enrollment/application/student_contracts.py, src/enrollment/application/ports.py and src/enrollment/domain/: all new Core modules scanned, no external type/Any/framework leakage, Domain owns required text/key/self-exclusion, Application only coordinates, and enrollment UoW gains no Student writes. Include meaningful violating fixtures and behavioral converter review; retain strict mypy, Import Linter and whole Core statement/branch coverage at 100% including unchanged branches, with no new exclusion.
- [ ] T081 [P] Write and execute failing evidence-completeness tests in tests/architecture/test_quality_gates.py for scripts/assemble_evidence.py and scripts/check_evidence.py: require exact enrollment scenario identities plus all seven student-detail families and their declared parameter variants; reject missing/duplicate/skipped new cases, absent/unordered/failed new increment stages, stale/tampered artifacts, empty/unimported Core scope, incomplete coverage and failed historical review. A family-presence or total-count-only check cannot pass a missing variant. Preserve existing negative gate fixtures and do not implement gate changes before their expected failures.
- [ ] T082 Implement only T081-driven gate changes in scripts/assemble_evidence.py and scripts/check_evidence.py, with explicit expected test identities/increment mappings and named scenario sets in the final manifest. Bind each new per-behavior ordered Red/Green/Refactor transcript and source association while retaining historical evidence. Assembly captures failures truthfully and remains separate from validation; no lowering coverage, approving historical review, ignoring skipped tests, reusing old Red or changing REQUIRED_INCREMENTS merely to accept absent evidence. Rerun T081 checks Green/refactor and preserve fresh gate-cycle evidence.
- [ ] T083 Update README.md, specs/001-enroll-course/quickstart.md and specs/001-enroll-course/evidence/README.md with tested host Python integration usage, full required Student fields, production connection-function registration, fresh/compatible initialization, explicit refusal of legacy schemas and external migration responsibility. Document unchanged enrollment endpoint and the exact checks -> review/assembly -> validation sequence; execute the documented validation commands and correct only verified guide defects.
- [ ] T084 Execute scripts/check-quality.sh against the final source/config/test state, including all acceptance families, new internal integration tests, real socket and installed-wheel checks, architecture, Import Linter, strict mypy, Ruff and complete Core coverage at 100%. Capture raw results under specs/001-enroll-course/evidence/final/checks/ without requiring a pre-existing manifest; preserve failed attempts. Any later source/test/config edit invalidates this capture and requires T084 onward again.
- [ ] T085 Inspect every required new per-behavior transcript plus the unresolved historical findings in specs/001-enroll-course/evidence/review.json; record a truthful extension review and preserve the original failed review under specs/001-enroll-course/evidence/history/ before any review-file update. Do not set overall passed=true while the T050 process limitation remains unresolved under the constitution; new successful cycles cannot repair missing historical ordering. Report remaining blockers without changing history or manufacturing Red, and leave completion-dependent tasks pending if no valid resolution exists.
- [ ] T086 Assemble specs/001-enroll-course/evidence/final/manifest.json through scripts/assemble_evidence.py after T084 and truthful review capture: include both required scenario sets, all declared variants, ordered historical/new increment references, exact final source/config/test digest and actual raw check/artifact hashes. Preserve old evidence before replacing final artifacts; include failed/missing review truthfully rather than omit it. Assembly itself is not a pass and may proceed to record a blocked state.
- [ ] T087 Execute scripts/check_evidence.py on specs/001-enroll-course/evidence/final/manifest.json and retain specs/001-enroll-course/evidence/final/validation.json. Require complete consistent fresh checks/scenarios/variants/increments and passed review; if T050's limitation persists, report the failure and keep T050/T087 completion pending. Never waive it through this task. Declare feature completion only after final quality, evidence review and validation genuinely pass; rerun T084 -> T085 -> T086 -> T087 after relevant final-state changes.

## Extension dependencies and execution order

```text
T051 -> T052 -> T053
             -> US2 T054 acceptance Red
             -> T055 name -> T056 email -> T057 Student -> T058 policy
             -> T059 contracts -> T060 create -> T061 invalid input
             -> T062 operation modes -> T063 email outcomes
             -> T064 configured connections -> T065 constrained schema
             -> T066 initialization -> T067 reconstitution -> T068 student UoW
             -> T069 conflict translation -> T070 real integration
             -> T071 concurrent claims -> T072 replacement races
             -> T073 failures -> T074 direct constraints -> T075 US2 verified
T075 -> US1 T076 fixtures -> T077 HTTP regression -> T078 protocol -> T079 packaging/socket
T079 -> (T080 architecture || T081 evidence Red) -> T082 evidence Green
     -> T083 docs -> T084 final checks -> T085 honest review
     -> T086 manifest -> T087 validation
Historical unresolved T050 review limitation -----------------------> blocks final pass
```

Setup/foundation block story implementation, not research. New task IDs follow the existing 50 tasks. Phase 7 implements US2 first because it supplies the valid record/schema consumed by equal-priority US1's extension regression in Phase 8. US2 can be validated without HTTP; US1 can be validated without invoking the student-write integration capability, using valid prepared records. Shared types and sqlite.py mean the production story changes are sequential. No workflow can infer historical T050 completion from new check results.

### Parallel opportunities and examples

US2: after T054, separate test-only drafting in tests/domain/test_student_values.py and tests/domain/test_student_policies.py is possible, but T055–T058 remain sequential because they share values.py/outcomes.py and required evidence ordering. These drafts do not complete implementation tasks or count as executed Red. Do not concurrently edit the acceptance harness or sqlite.py.

US1: after T076, test-only preparation in tests/acceptance/test_student_record_integrity.py and tests/adapters/test_graphql.py can be separate; T077 and T078 still execute in order and adapter corrections must remain serialized. Real socket tests are not parallel with fixture changes. No story production task is marked [P] because its prerequisites/shared-file writes overlap.

After both story checkpoints, T080 and T081 are the two [P] tasks: tests/architecture/test_boundaries.py versus tests/architecture/test_quality_gates.py are disjoint. T080 must not edit source files shared with another task; make any driven production correction sequentially, rerun affected story suites and restart final capture as needed. T082 waits for T081's actual Red, and final gates wait for both. Parallel drafting/execution examples are scheduling guidance, not a request to spawn agents during task generation.

## Extension traceability

| Requirement / scenario | New owning tasks |
|---|---|
| FR-011; US2 1–2; SC-005 | T054–T057, T059–T062, T064–T067, T070, T074–T075 |
| FR-012; US2 3–6; SC-006 | T056, T058, T063–T065, T068–T072, T074–T075 |
| FR-013; US2 2, 3, 6, 7; SC-007 | T059–T063, T067–T073, T075 |
| Name non-unique; full original text; no syntax/normalization additions | T055–T057, T065, T070, T074 |
| Self-exclusion, cross-programme and Unicode whole-address matching | T056, T058, T063, T065, T070–T072, T074 |
| Corrupt restoration, legacy refusal, compatible initialization | T066–T067, T074, T077, T083 |
| FR-001–FR-010 / SC-001–SC-004; all US1 scenarios | T076–T079 plus preserved T010–T043 |
| Unchanged SDL, no Student writes during enrollment | T059, T068, T076–T080 |
| Constitution I–II: owned policies/ports and explicit bridges | T055–T069, T077–T080 |
| Constitution III–V: per-behavior TDD, full coverage, truthful final evidence | T051–T054, every behavioral task, T080–T087; historical T050 remains open |

Every new local field constraint is quoted in T055–T057/T065; unchanged ID/programme constraints remain in historical T011/T013 and are preserved by T057/T059. Tests in the owning tasks cover construction, restoration and full replacement, not only happy-path admission.

## Extension implementation strategy and MVP

1. Record the actual baseline and initialize fresh evidence. Do not repeat project scaffolding or dependency selection. Preserve all historical checked markers and the failed review.
2. Build US2 outside-in as small independent Red/Green/Refactor cycles, beginning with executable acceptance. First demonstrate one retained valid record; then complete required-text rejection, global/self email policy, real storage constraints, atomic writes and failure/concurrency guarantees. The first success alone is an interim demonstration.
3. Validate all seven US2 families through the Python host boundary, then adapt the existing US1 fixtures and prove all fifteen enrollment scenarios through HTTP. Keep provisioning separate from enrollment so each story is independently testable.
4. The extension MVP is the complete US2 plus US1 compatibility and mandatory final gates. The original US1-only MVP already exists; delivering only that does not satisfy the requested required-attribute extension. No management website, GraphQL mutation or migration project is included.
5. Run and capture final quality, inspect honest evidence, assemble and validate the final manifest. Preserve and report T050's process nonconformance until legitimately resolved; no new task authorizes a waiver. Task generation does not claim runtime checks passed, approve a review, or implement production behavior.
