# Tasks: Student Self-Enrollment

**Input**: Design documents in `specs/001-enroll-course/`.
**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contract](contracts/enrollment-api.md), [SDL](contracts/schema.graphqls), [quickstart.md](quickstart.md); Constitution v1.3.0.
**Tests**: Mandatory Outside-In TDD under the constitution and the user's prior instructions. Implementation status is tracked by the checked task markers below.
**Organization**: One story, US1 (P1); Setup -> Foundational -> US1 -> final verification. Paths below are repository-relative.

## Format and execution rules

Tasks use `- [ ] Tnnn [P?] [US1?] description with paths`. [P] means independent files/work after stated prerequisites, not permission to bypass test-first ordering. Story tasks always carry [US1]; shared/final tasks do not.

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


## Execution outcome

The functional implementation and final quality capture pass: 148 tests, all fifteen numbered acceptance scenarios, 100% complete Core statement/branch coverage, strict mypy, Ruff and five Import Linter contracts. T048 captured raw results and T049 assembled the matching manifest.

**T050 remains incomplete.** Evidence validation was executed and failed closed solely because the review did not pass. Several early increments used grouped Red suites followed by grouped implementations, so the recorded history does not fully demonstrate the required per-behavior Red–Green–Refactor execution order. Checked delivery markers above do not resolve that process nonconformance or imply feature completion. See [review](evidence/review.json) and [final validation](evidence/final/validation.json). No historical result was rewritten or manufactured to claim compliance.

## Dependencies and execution order

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

Only US1 exists; there are no invented US2/US3 phases or cross-story dependencies. All entities, ports and external contracts serve US1. Setup/foundation deliberately avoid implementing business behavior before the first acceptance failure.

### Parallel opportunities and example for US1

T003 and T004 can run concurrently after T002: `.gitignore` and evidence documentation are disjoint. Shared pyproject.toml changes remain sequential.

Within US1, the production package is small and shared files overlap, so no story task is marked [P]. After T017, a limited parallel preparation example is drafting the independent `tests/adapters/test_identity_bridge.py` and `tests/adapters/test_graphql.py` assertions for T028/T030 in separate files. These drafts do **not** complete those tasks: their dependencies, executed behavioral Red and later Green remain in the stated order. Never parallelize writes to enroll.py/sqlite.py/bootstrap.py, share evidence files between workers or count a draft test as executed evidence. This is an execution option, not an instruction to spawn agents during task generation.

## Requirements and scenario traceability

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

## Implementation strategy

1. Complete Setup and Foundational checks. Keep production free of business behavior until T010 acceptance Red.
2. Drive US1 outside-in: acceptance -> failing inner behavior -> minimum implementation -> refactor, repeating independently for each behavior. Core models precede orchestration implementation; adapters integrate afterward while acceptance guides the work.
3. Demonstrate the first durable eligible enrollment as an interim slice, then complete every specified rejection, race, retry and failure case. Do not call the interim success slice the completed MVP.
4. MVP is the **entire US1** plus mandatory final checks: one enrollment mutation, existing identity dependency, real SQLite and all fifteen acceptance examples. No UI, account/record management, capacity, terms, withdrawals or extra infrastructure.
5. Complete T048 quality execution/capture, then T049 manifest assembly, then T050 evidence validation and reviewer inspection on the final implementation state. A check result, an assembled manifest or a passing stage alone never implies completion. Task generation alone does not authorize deployment or claim any runtime check passed.
