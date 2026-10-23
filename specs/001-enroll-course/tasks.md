---
description: "Remaining Student Self-Enrollment work for Constitution v3.0.0 and conditional Student replacement"
---

# Tasks: Student Self-Enrollment

**Input**: Design documents from `/specs/001-enroll-course/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md), [ADR-0001](adr/0001-entity-lifecycle-and-student-revisions.md), and Constitution v3.0.0.

**Tests**: Required by the specification and constitution. Use acceptance-guided Outside-In TDD with cohesive Red → Green → Refactor increments. Execute a relevant behavioral acceptance failure before production changes, then any relevant inner-layer Red before its implementation. Missing imports/signatures, empty selections, environment failures, and unrelated failures do not count as Red. Record already-passing behavior as verification; never manufacture historical Red.

**Organization**: Only remaining work is open here: T130–T181. Completed T101–T129 are preserved byte-for-byte in [history/tasks-v231.md](history/tasks-v231.md), SHA-256 `7d065388305f7450c51fc48d9a22078d37d23e6f9ec2504fbc060385178a5d11`. T001–T100, C1/T050, Unicode verification and prior evidence remain in Git/history and the existing evidence tree. This task-generation operation does not recertify or rewrite them.

**Current implementation**: Python 3.12, Flask, graphql-core, Waitress, SQLite, typed factories/reconstitution, Unicode comparisons, integrity mapping and recorder state/test/activity fields already exist. Keep them and `pyproject.toml`/`uv.lock`; do not recreate the project or upgrade dependencies. Remaining gaps are Entity-taking writes and Application Entity construction, saved versions/snapshots/conditional writes, schema compatibility, Repository-only call-site enforcement, exact acceptance inventory and new-increment evidence validation.

## Format: `[ID] [P?] [Story] Description`

- Each task has an unchecked checkbox, unique sequential ID and exact repository-relative file paths.
- `[P]` permits concurrent work on different files only after the prerequisites stated below. Execute evidence runs against a stable tree; parallel test authoring does not authorize concurrent edits during recorded runs.
- `[US1]` and `[US2]` label only tasks in their corresponding story phases. Both stories are P1; retain specification order.

## Path Conventions

- Production: `src/enrollment/{domain,application,adapters}/` and `src/enrollment/bootstrap.py`.
- Verification: `tests/{acceptance,domain,application,adapters,architecture}/` and `tests/support/`.
- Evidence tooling: `scripts/`; feature design/history/evidence: `specs/001-enroll-course/`.
- `tests/adapters/test_repository_lifecycle.py` is a new focused contract file; other named files already exist. Add no new framework, reservation schema, Entity lifecycle handle or management endpoint.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Preserve the implemented baseline and identify exactly what remains, without rerunning completed migration tasks as new development.

- [X] T130 Before modifying existing evidence, identify and archive the current `specs/001-enroll-course/evidence/final/`, `specs/001-enroll-course/evidence/reconciliation/review.json`, and every other existing evidence file that subsequent tasks will modify or overwrite, including `specs/001-enroll-course/evidence/README.md`; preserve original file bytes under `specs/001-enroll-course/evidence/history/pre-v300-alignment/` with paths relative to `evidence/`, compute each source SHA-256 before modification and verify each archived copy against that source hash, and retain every existing historical file unchanged; record the implementation digest from `scripts/record.py`, Git revision, Python version and verified archive/source hash index in `specs/001-enroll-course/evidence/reconciliation/v300-baseline.json`; a hash index alone is not preservation, and no dependent modification may begin before the corresponding archived bytes are verified
- [X] T131 Run the existing acceptance and relevant architecture/Repository suites through `scripts/record.py` as verification, record exact existing node IDs and scenario/parameter mappings in `specs/001-enroll-course/evidence/reconciliation/v300-baseline-inventory.json`, and report existing failures/environment limits without labeling them behavioral Red
- [X] T132 Define required cohesive increments and their acceptance/inner-test associations in `specs/001-enroll-course/evidence/reconciliation/v300-increments.json`, and document capture commands and historical classification in `specs/001-enroll-course/evidence/README.md`; use distinct increment names for Repository/enrollment lifecycle, Student snapshots/schema, conditional replacements, and gate hardening, retaining existing recorder metadata and positional CLI

**Checkpoint**: Original implementation/evidence and every existing acceptance variant are identifiable. No dependency or business behavior has changed.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Make the existing evidence gate distinguish new required work from historical records before implementing either story. This phase adds no business behavior or Entity construction abstraction.

- [X] T133 Add and execute failing evidence-tool contract tests in `tests/architecture/test_quality_gates.py` at the existing `validate`/assembly boundary: a required new increment with absent/defaulted state, missing/mismatched test/activity associations, unrelated Red/Green, reversed/overlapping execution, changed-during-run state, failing Green or historical-only records must fail; explicitly add regression tests for `scripts/record.py::_test_id()` and captured records that distinguish direct pytest executables and `python -m pytest` executable/module arguments from meaningful test paths, pytest node IDs and `-k` expressions, retain combined selector/filter context, reject executable-only identities whether inferred or explicitly supplied, and preserve meaningful new-TDD test relevance associations; multi-test selections must be identified as selections and must not claim one specific executed test unless that test is independently identified by execution evidence; a consolidated associated acceptance-first increment with distinguishable subsequent inner cycles and honest selection identities must pass
- [X] T134 Harden `scripts/check_evidence.py` after T133 Red so the required v3.0.0 increment set comes explicitly from the manifest/review and cannot be satisfied by the historical compatibility path; enforce the required associations, relevant acceptance-first chronology and ordered nonoverlapping Red/Green while permitting honestly classified historical records without rewriting them
- [X] T135 Update `scripts/assemble_evidence.py` after T133 Red to carry the required-increment declaration and its hashed reference from `specs/001-enroll-course/evidence/reconciliation/v300-increments.json`, separate historical records from new required execution records, and fail closed on omitted/unknown required associations without fabricating execution results
- [X] T136 After T133's recorded regression failures, correct `scripts/record.py::_test_id()` and any necessary capture validation so pytest executable/module arguments cannot become test identities; retain meaningful test-path, pytest-node-ID and `-k` expression selections with their combined context, reject executable-only identities, and represent multi-test commands as selections rather than a claimed specific test execution unless that test is independently identified by execution evidence; run the positive/negative recorder and evidence fixtures in `tests/architecture/test_quality_gates.py`, require new TDD records to retain meaningful relevance associations, record Green and refactoring consideration through the corrected `scripts/record.py`, and document the corrected capture behavior in `specs/001-enroll-course/evidence/README.md`; preserve existing state/activity metadata and positional CLI, and leave historical evidence unchanged
- [X] T137 Translate the contract's precise returned creation/transition outcomes and transaction states into a review checklist in `specs/001-enroll-course/evidence/reconciliation/v300-contract-map.md`, linking `contracts/repository-lifecycle.md`, `contracts/domain-construction.md`, `contracts/enrollment-api.md` and `contracts/student-details.md`; distinguish known active-uncommitted, confirmed commit and uncertain commit, with no success before confirmed commit or destructive compensation afterward

**Checkpoint**: Gate-tool contract tests pass and new work cannot inherit historical TDD proof. All story implementation depends on T137.

---

## Phase 3: User Story 1 — Student Self-Enrollment (Priority: P1) — Enrollment MVP

**Goal**: Repository confirms natural/composite identities before complete Entity construction; enrollment keeps its public GraphQL contract, ordered policy decisions, atomic creation and commit boundary.

**Independent Test**: HTTP POST `/graphql` through Flask, real graphql-core, credential headers, injected verifier and real temporary file-backed SQLite. All `enrollment-1`–`enrollment-19` families retain the approved outcomes. Explicit rejection/exception after INSERT and definite commit failure expose no success or partial enrollment; a valid historical pair remains readable after eligibility changes. US2 subsequently adds saved-version validation to every Student read; that shared metadata extension is not a prerequisite for exercising these enrollment outcomes on the existing valid schema.

### Tests for User Story 1

> Execute T138 acceptance Red before production changes. T139–T141 may then be authored in parallel, followed by relevant inner Red. Cases that already pass are verification, not invented Red.

- [X] T138 [US1] Add and execute HTTP acceptance in `tests/acceptance/test_enrollment.py` for `enrollment-16` (explicit factory rejection and exception after acknowledged INSERT), `enrollment-17` (definite failed commit), `enrollment-18` (restore a saved pair after membership/offering changes), and `enrollment-19` (unusable CourseId plus missing Student/Programme, with denial taking precedence); also guide shared cleanup/uncertain-commit changes with technical-failure/no-compensation acceptance cases before T145, preserve scenarios 1–15, assert no disclosure/mutation and no precommit success, and record a genuine lifecycle behavioral Red through `scripts/record.py`; GraphQL schema-invalid nontext/missing values remain protocol errors, with raw-input counterparts tested at Application
- [X] T139 [P] [US1] Add Application port-double tests in `tests/application/test_enrollment_flow.py`, `tests/application/test_conflict.py` and `tests/application/test_failure_outcomes.py` for validated-value Repository requests, one enclosing commit, discarded pending results, cleanup failures overriding ordinary outcomes, primary exception preservation and exactly one full ordered pair-conflict replay; retain FR-009/FR-014 short circuits and technical failure on a second unresolved conflict
- [X] T140 [P] [US1] Add and execute real SQLite contracts in `tests/adapters/test_repository_lifecycle.py` for acknowledged INSERT before Entity factory use, actual stored identities, Domain acceptance before commit, duplicate constraints without overwrite, explicit factory rejection/exception rollback of preceding and following UoW writes, no Repository partial commit, and no successful/reusable canceled result; use a controlled factory seam when valid typed inputs have no genuine rejecting branch, rather than inventing a Domain rule
- [X] T141 [P] [US1] Extend invariant/restoration verification in `tests/domain/test_values.py` and `tests/domain/test_records.py`, quoting the model constraints: "StudentId, ProgrammeId, CourseId and SubjectId are exact nonempty strings; whitespace is not trimmed and case is not folded.", Programme has "Valid confirmed identity; existing prerequisite, no management use case added.", Course has "Valid confirmed identity; shared by multiple programmes.", Offering has "Both confirmed typed components; represents a persisted offering relationship.", and Enrollment has "Unique confirmed pair; new admission requires approved prerequisite/duplicate/offering policy sequence."; cover separate create/reconstitute invariants and historical restoration, while stating pure Domain tests do not prove persistence confirmation

### Implementation for User Story 1

- [X] T142 [US1] Replace Entity-taking `add` with `create_enrollment(StudentId, CourseId)` in `src/enrollment/application/ports.py`, update returned pending-Entity/PairConflict/applicable Domain-rejection types in `src/enrollment/application/contracts.py`, and migrate enrollment port doubles in `tests/support/application.py` and affected `tests/application/` callers; retain neutral Core-owned types, read operations, UoW ownership and no Student write method
- [X] T143 [US1] Implement `create_enrollment` in `src/enrollment/adapters/persistence/sqlite.py`: ordinary INSERT, obtain the actual separate student/course identity components from inserted state in the same transaction, then invoke `Enrollment.create` without committing; map only the exact pair constraint to PairConflict, propagate explicit Domain rejection, and leave all uncommitted changes rollback-capable
- [X] T144 [US1] Remove `Enrollment.create` from `src/enrollment/application/enroll.py`, invoke Repository with validated values after approved policies, keep the pending Entity local and return it only after confirmed enclosing commit; preserve verification → StudentId → ownership → CourseId → Student → Programme → Course → duplicate → offering order and the bounded fresh full pair-conflict replay
- [X] T145 [US1] Harden transaction cleanup in `src/enrollment/application/cleanup.py` and `src/enrollment/adapters/persistence/sqlite.py` using the T139/T140 failures: SQL `BEGIN IMMEDIATE` before reads, explicit SQL `COMMIT`/`ROLLBACK` with Python 3.12 `autocommit=True`, five-second timeout and worker-owned connections; rollback only known active uncommitted work, surface cleanup failure over ordinary outcomes, preserve propagating exceptions with diagnostics, discard unpublished results on uncertain commit and never delete/revert potentially committed rows
- [X] T146 [US1] Keep complete prerequisite Entity creation/restoration inside persistence Repository implementations in `src/enrollment/adapters/persistence/sqlite.py`; add only trusted provisioning helpers needed by complete-Entity callers for Programme/Course/Offering using INSERT → stored identity → factory, retain row-based reconstitution and None for absence, and migrate `tests/support/database.py` and affected `tests/adapters/test_sqlite.py`/`tests/adapters/test_transactions.py` callers without adding management use cases or lifecycle handles
- [X] T147 [US1] Add and execute HTTP acceptance in `tests/acceptance/test_persistence_failure.py` and `tests/acceptance/test_retry.py` for uncertain commit and confirmed response loss as distinct events, then satisfy any demonstrated gaps in `src/enrollment/application/enroll.py`, `src/enrollment/application/cleanup.py` and `src/enrollment/adapters/persistence/sqlite.py`; require sanitized technical failure without inferred success, later independent reconciliation, durable confirmed rows and existing retry precedence, recording acceptance/inner Red → Green before each changed behavior
- [X] T148 [US1] Extend real-persistence fault and outer-boundary tests in `tests/adapters/test_repository_lifecycle.py`, `tests/adapters/test_transactions.py`, `tests/adapters/test_graphql.py` and `tests/adapters/test_http.py` for insertion/commit/rollback/close faults, preservation of unexpected programming errors, precise conflicts and operation-local pending results; run behavioral Red before any additional fixes and keep the SDL in `src/enrollment/adapters/graphql/schema.graphqls` identical to `specs/001-enroll-course/contracts/schema.graphqls`
- [X] T149 [US1] Preserve and verify serialized eligibility changes, same-pair races and unrelated valid work in `tests/acceptance/test_concurrency.py`, `tests/acceptance/test_eligibility_races.py`, `tests/acceptance/test_retry.py` and `tests/adapters/test_server.py`; use bounded events and separate worker-owned connections, never sleeps or a two-party barrier after the writer lock, and route supported Student membership changes through the current host operation, ready for explicit versions in US2
- [X] T150 [US1] Extend the enrollment portion of `scripts/acceptance_inventory.py` with exact node-ID/scenario mappings for `enrollment-1`–`enrollment-19`, including retained original variants and auxiliary race/retry coverage from T131; attach stable scenario properties in `tests/acceptance/test_enrollment.py` and any mapped supplementary acceptance files without weakening existing behavioral assertions
- [X] T151 [US1] Record acceptance/inner Green and refactoring consideration using `scripts/record.py`, then verify `tests/acceptance/`, `tests/application/`, `tests/adapters/` and relevant Domain tests in `specs/001-enroll-course/evidence/reconciliation/v300-us1-checkpoint.json`; confirm the unchanged SDL, 19 enrollment families and existing Student regression behavior, and report that saved-version schema/host integration and final v3.0.0 certification remain pending US2/Polish

**Checkpoint**: Enrollment lifecycle is independently demonstrated at HTTP and Repository boundaries. This is an enrollment MVP, not completion of both P1 stories or v3.0.0 certification. No old Entity-taking enrollment write remains.

---

## Phase 4: User Story 2 — Valid Student Details (Priority: P1)

**Goal**: Trusted hosts read committed Student snapshots, create through Repository identity confirmation, and fully replace only the saved version originally read. Existing name/email and global Unicode uniqueness behavior remains intact.

**Independent Test**: Call `save_student`/`get_student` with real file-backed SQLite independently of enrollment. Verify all `student-details-1`–`student-details-17` families and every original parameter variant, version 1 creation, one winner/one stale conflict for same-version races, unchanged details/version on rejection or definite failure, and deliberate reload before retry. No new GraphQL operation or outcome is introduced.

### Increment A: Student snapshots, versions and schema

> T152 is the outer acceptance Red. T153–T155 may then be authored in parallel on separate files. Stage schema/fixture and host changes as one migration increment; the next full regression checkpoint is T174, after conditional replacements are implemented. Never provide an interim unconditional replacement fallback.

- [X] T152 [US2] Add and execute `student-details-11`–`student-details-13` acceptance in `tests/acceptance/test_student_details.py` through the existing `save_student` boundary: committed creation returns supplied identity/details plus saved version, post-INSERT rejection/exception/definite failure exposes no Student, and failed replacement preserves complete prior details/version; include an initial stale-replacement rejection to guide the Domain policy before T157, begin with behavioral snapshot/confirmation assertions on the existing return value rather than import/signature failure, then add `get_student` round-trip/read consistency checks as its API becomes available
- [X] T153 [P] [US2] Add and execute SavedVersion input/restoration, Domain outdated-version policy, Student transition and equality/hash tests in `tests/domain/test_student_values.py`, `tests/domain/test_policies.py` and `tests/domain/test_records.py`, including valid boundaries, bool/noninteger/range rejection, existing typed factories and original text/email semantics; record relevant inner Red after T152
- [X] T154 [P] [US2] Add and execute schema/Repository contracts in `tests/adapters/test_student_uow.py` and `tests/adapters/test_sqlite.py` for strict saved versions, advancement guard, idempotent compatible initialization, refusal of legacy/missing/wrong constraints/guard or invalid stored versions before any mutation, initial version 1, stored-identity-before-Student.create and real rollback after factory rejection/exception; compare database schema/data before and after refused initialization
- [X] T155 [P] [US2] Add and execute trusted-boundary tests in `tests/application/test_student_details.py` for snapshot consistency, raw-ID get_student validation, missing target, read commit then close before return, no lazy connection, create ignoring supplied expected_version, known storage/integrity failure and unexpected exceptions; verify mode stays after four field validations and no complete Student is constructed by Application
- [X] T156 [US2] Add `InvalidSavedVersion`/`OutdatedVersion` to `src/enrollment/domain/outcomes.py` and SavedVersion factories/reconstitution to `src/enrollment/domain/values.py`, preserving verbatim constraints: "SavedVersion is a Domain Value Object containing an integer from 1 through 9,223,372,036,854,775,807.", "Bool, missing input, strings, floats and out-of-range values are invalid; no coercion.", and "Normal input returns InvalidSavedVersion, restoration returns InvalidPersistedState."; do not change existing Value Object creation APIs
- [X] T157 [US2] Implement the pure expected/current SavedVersion policy in `src/enrollment/domain/policies.py` and controlled `Student.replace_details` in `src/enrollment/domain/models.py`; preserve "immutable identity, equality/hash by StudentId only.", "Programme existence is not a construction/restoration invariant.", "StudentName and StudentEmail require actual strings with a non-whitespace character under the existing Python 3.12 text rules.", "Preserve original text.", "StudentEmail equality/hash uses complete `str.casefold()` output, including multi-character expansions; whitespace, Unicode composition, dots and plus tags are not normalized.", and "Names are not unique."; Domain performs no I/O and gains no transaction handles
- [X] T158 [US2] Define frozen `StudentSnapshot(student, saved_version)` and precise returned write observations in `src/enrollment/application/student_contracts.py`, and replace Entity-taking save/student-only reads with snapshot/create_student/replace_student Ports in `src/enrollment/application/student_ports.py`; enforce "Immutable Application result containing a Repository-issued Student and SavedVersion from one saved row/atomic operation." with no redundant copied fields or external types, mandatory typed expected_version for replace, and distinct VersionConflict/EmailKeyConflict/existence observations
- [X] T159 [US2] Extend `src/enrollment/adapters/persistence/schema.sql` with "Student saved_version is NOT NULL INTEGER with strict SQLite `typeof(...)=integer` and positive signed-64 range." and "A validation-only BEFORE UPDATE guard rejects any Student update whose new saved_version is not exactly the previous value plus one, including unchanged-detail writes."; retain all five business keys/foreign keys, required text, global `students_email_key` and dangling Student programme semantics, add no reservation table/default old-row version, and reject maximum-version floating-point promotion
- [X] T160 [US2] Inspect existing schema/constraints/guard and stored versions before DDL/data mutation in `src/enrollment/adapters/persistence/sqlite.py`, refuse incompatible databases unchanged, retain idempotent compatible initialization and Domain-backed `required_text`/`email_key` on configured connections, and translate known schema faults into Core storage/integrity categories without migration/backfill or fabricated details
- [X] T161 [US2] Implement one-row snapshot restoration and INSERT-based `create_student` in `src/enrollment/adapters/persistence/sqlite.py`: "Repositories insert 1 explicitly for fresh Students; no silent version assignment is applied to existing schemas.", obtain actual inserted StudentId before Student.create, validate saved_version on every Student restoration including enrollment-only reads, map corruption to DataIntegrityFailure and missing rows to None, return only pending snapshots to the enclosing operation and never independently commit
- [X] T162 [US2] Implement `get_student` and the create branch of `save_student` in `src/enrollment/application/student_details.py` using the new Ports, remove Application Student factory calls, validate raw values in approved order, commit and close read transactions before returning detached snapshots, and expose successful create snapshots only after enclosing commit; preserve existence/email precedence, no programme-existence rule and current technical/exception handling

### Increment B: Conditional full replacement and races

> Execute T163 acceptance Red before authoring and running T164's inner contracts or implementing replacement. Do not treat the changed command signature as the behavioral failure.

- [X] T163 [US2] Add and execute `student-details-14`–`student-details-17` acceptance in `tests/acceptance/test_student_details.py`: same-version replacements produce one winner/one OutdatedVersion, deliberate reload/retry succeeds unless another update intervenes, missing/unusable expected_version preserves committed state, and old-version retry after lost committed response is outdated; include identical-detail advancement, A→B→A without token reuse, stale-before-email, missing-target-before-stale and uncertain commit without compensation
- [X] T164 [US2] Add and execute conditional Repository/Application contracts in `tests/adapters/test_student_uow.py` and `tests/application/test_student_details.py` for a full identity+version guarded write, defensive zero-row VersionConflict, precise email conflict versus unrelated SQL error, no automatic reload/replay, maximum-version technical failure without changes, cleanup-over-ordinary-result and primary exception preservation; race tests use separate connections and bounded synchronization
- [X] T165 [US2] Implement the replace branch in `src/enrollment/application/student_details.py`: validate StudentId → ProgrammeId → name → email → mode → required raw expected_version, then target existence → Domain outdated-version policy → Domain email policy → Repository replacement; pass typed values rather than Entities, translate defensive VersionConflict to OutdatedVersion and precise EmailKeyConflict to EmailConflict, and return a snapshot only after confirmed commit with no silent refresh/retry
- [X] T166 [US2] Implement `replace_student` in `src/enrollment/adapters/persistence/sqlite.py` through controlled `Student.replace_details` on the confirmed identity and one full UPDATE matching StudentId and expected saved_version, advancing version in the same statement; preserve "Even identical-detail replacement consumes a new saved version; old field values restored later cannot revive an old token." and "Reaching the maximum on a requested replacement is a technical persistence limitation: no update, no version wrap/reuse."; return pending snapshots/precise conflicts, never delete/reinsert or commit inside Repository
- [X] T167 [US2] Migrate original `tests/acceptance/test_student_details.py`, `tests/application/test_student_details.py` and `tests/adapters/test_student_uow.py` callers to snapshot results and explicit raw `snapshot.saved_version.value` on replacement, obtaining it from the originally read state rather than auto-refreshing inside stale/race helpers; preserve every original assertion/parameter identity unless an approved result-shape change requires adaptation and retain all original Unicode variants
- [X] T168 [US2] Update valid Student provisioning/seeds and membership-change fixtures in `tests/support/database.py`, `tests/conftest.py`, `tests/acceptance/test_eligibility_races.py`, `tests/adapters/test_server.py` and other actual callers found by repository search to explicitly create version 1 and use conditional host updates for existing Students; keep intentional corrupt-database tests isolated from production schema/configuration and do not weaken valid constraints or disable same-thread protection
- [X] T169 [US2] Extend integrity tests in `tests/acceptance/test_student_record_integrity.py` and `tests/adapters/test_sqlite.py` for corrupt saved_version through both host and enrollment restoration, preserve original invalid-text/Unicode-whitespace tests using isolated corruption fixtures, and verify dangling programmes and historical enrollments still restore without current admission/email checks; execute acceptance/inner Red before fixing any remaining restoration gaps in `src/enrollment/adapters/persistence/sqlite.py`
- [X] T170 [US2] Extend real-persistence creation/transaction tests in `tests/adapters/test_repository_lifecycle.py` and `tests/adapters/test_transactions.py` for Student duplicate identities, exact email-key collisions, whole-UoW rollback after explicit Domain rejection and exception, failed replacement preservation, definite/uncertain commit and cleanup failures; verify pending snapshots never escape through results, callbacks, caches or exception payloads and no uncertain/confirmed commit causes deletion/reversion
- [X] T171 [US2] Extend `scripts/acceptance_inventory.py` with exact `student-details-1`–`student-details-17` node-ID/scenario mappings, preserving every baseline variant from T131 including all original cases plus Unicode expansion/composition, and update stable scenario properties in `tests/acceptance/test_student_details.py`; do not substitute collection counts for exact identities
- [X] T172 [US2] After relevant failing tests, resolve remaining typed result/port wiring in `src/enrollment/application/student_contracts.py`, `src/enrollment/application/student_ports.py`, `src/enrollment/bootstrap.py` and actual host integration callers identified by search, ensuring new InvalidSavedVersion/OutdatedVersion/Snapshot results never enter enrollment SDL or reason mappings and no Entity-taking Student write/unconditional supported replacement remains
- [X] T173 [US2] Record acceptance/inner Green and refactoring consideration for snapshot/schema and conditional replacement increments through `scripts/record.py`, verify all 17 Student families and real same-version/email races, and write `specs/001-enroll-course/evidence/reconciliation/v300-us2-checkpoint.json` with exact node identities, successful revision advancement and preserved committed state on rejection/failure
- [X] T174 [US2] Run both stories together using `tests/acceptance/`, `tests/domain/`, `tests/application/`, `tests/adapters/` and current `tests/architecture/`, record results through `scripts/record.py`, and resolve demonstrated compatibility regressions in the owning implementation/test task without weakening tests; verify enrollment never changes Student details/versions and both boundaries remain independently callable without Flask context in Core

**Checkpoint**: Both P1 stories work with the versioned schema. Trusted hosts supply explicit expected versions; old/incompatible databases are refused unchanged. Full architecture, inventory and final-evidence gates still follow.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Enforce complete-Entity call sites and exact scenarios, review semantics, and collect final-state evidence. All story checkpoints must precede this phase.

- [ ] T175 Add and execute architecture fitness tests in `tests/architecture/test_boundaries.py` for Repository-only production Entity create/reconstitute, direct/aliased unsupported constructors/factory references, permitted Value Object boundary factories, pure Domain test exceptions and positive/violating fixtures; retain inward dependencies, Core/framework/type isolation and outbound independence, then migrate any remaining violating production call sites in `src/enrollment/` without restricting supported adapter Value Object use or treating dependency checks as semantic proof
- [ ] T176 Add and execute negative/positive exact-inventory/final-evidence fixtures in `tests/architecture/test_quality_gates.py`, then update `scripts/check_evidence.py` and `scripts/assemble_evidence.py` to require all 19 enrollment and 17 Student families plus every baseline variant, reject missing/duplicate/skipped/mislabeled scenarios and stale/tampered checks, and retain the strict new-increment/history distinction from T134/T135 with no count-only or legacy bypass
- [ ] T177 [P] Update `README.md`, `specs/001-enroll-course/quickstart.md` and `specs/001-enroll-course/evidence/README.md` with actual snapshot read/create/conditional replacement examples, raw expected_version conversion, schema refusal/provisioning obligations, transaction/reconciliation behavior and runnable checks; document GraphQL compatibility and historical evidence limitations without adding public management operations
- [ ] T178 [P] Record the semantic boundary/lifecycle/TDD review and historical evidence index in `specs/001-enroll-course/evidence/reconciliation/v300-review.json`, checking Domain policy ownership, INSERT-confirmation-before-factory, operation confinement, one commit boundary, corruption/failure translation, uncertain-commit reconciliation, conditional-write precedence and state-associated chronology; recheck archived task/evidence SHA-256 values and explicitly report missing historical associations without manufacturing them
- [ ] T179 Run `bash scripts/check-quality.sh` against the stable final implementation and require passing acceptance/regression/Repository/architecture tests, installed-wheel resources, Waitress socket/concurrency checks, exact scenario variants, strict mypy, Ruff lint/format, Import Linter and complete Domain/Application 100% statement-and-branch coverage from `pyproject.toml`; include new/unimported Core files and whole affected methods, permitting only validated pure-Protocol ellipsis exclusions, and retain raw results under `specs/001-enroll-course/evidence/final/checks/`
- [ ] T180 Require T130's verified byte-preserving archive of the original `specs/001-enroll-course/evidence/reconciliation/review.json` at `specs/001-enroll-course/evidence/history/pre-v300-alignment/reconciliation/review.json`, plus every other pre-existing evidence file this task will overwrite; an archive hash index without the original bytes does not satisfy this prerequisite; then update `specs/001-enroll-course/evidence/reconciliation/v300-review.json` and the active `specs/001-enroll-course/evidence/reconciliation/review.json` to reference the T179 digest, required increments, exact inventory and actual passed/failed findings, and run `.venv/bin/python -m scripts.assemble_evidence` to produce `specs/001-enroll-course/evidence/final/manifest.json` with hashed current review/declaration/check/record references, leaving the verified historical copies unchanged
- [ ] T181 Run `.venv/bin/python -m scripts.check_evidence`, require `passed: true` in `specs/001-enroll-course/evidence/final/validation.json`, and compare the manifest/check/review digest to the final implementation; if any mandatory result is failed, skipped, blocked, missing or stale, fix its owning task and rerun T179–T181 after any source/test/config change before claiming feature completion

---

## Requested follow-up: Simplify Value Object construction

Scope: share `.create()` for Value Object input and persisted-state validation when
the invariants coincide. Preserve separate Entity `.create()` and `.reconstitute()`
lifecycle APIs. This follow-up does not close the unfinished Phase 5 tasks.

- [X] T182 Verify persistence uses Value Object `.create()` for valid and invalid identifiers, text and saved versions, translating invalid outcomes into DataIntegrityFailure; record the focused failure before implementation.
- [X] T183 Remove redundant Value Object `.reconstitute()` methods, update persistence decoding and affected Domain/architecture tests, and align README, plan, data model and Domain construction contract with the shared validated factory.
- [X] T184 Run focused and full regression/architecture/static/coverage checks, preserve Entity lifecycle and corruption behavior, and record the scoped refactoring verification without claiming broader feature completion.

Follow-up verification: 265 focused acceptance/Domain/Application/Repository/architecture
tests pass, as do the installed-wheel and real-socket tests after rerunning with the
required permissions. Domain/Application statement and branch coverage is 100%;
mypy, Ruff lint, Import Linter and changed-file formatting pass. The full suite
still has 22 failures in the existing evidence-tool tests, and repository-wide
formatting flags the untouched `tests/architecture/test_quality_gates.py`.
These broader issues remain with Phase 5. Scoped execution records and limitations
are indexed in `evidence/reconciliation/vo-construction-review.json`.

## Dependencies & Execution Order

### Phase Dependencies

```text
Setup T130–T132
  -> Foundation T133–T137
  -> US1 T138–T151 (enrollment MVP checkpoint)
  -> US2 T152–T174 (both P1 stories, versioned schema)
  -> Polish T175–T178
  -> Final checks T179 -> review/assembly T180 -> validation T181
```

US1 starts only after T137. US2 starts only after T151 has been recorded: shared persistence, model, cleanup and acceptance helper files require sequential migration. US2 is independently testable through the Python host boundary despite this implementation dependency. US1's checkpoint uses the existing valid Student schema; T159–T169 add saved-version constraints/restoration to the shared persistence implementation, and T174 revalidates enrollment against it. No full v3.0.0 completion or versioned host release is claimed at the US1 checkpoint.

### Within Each Story

- US1: acceptance T138 → inner tests T139/T140/T141 → Ports T142 → Repository T143 → orchestration T144 → cleanup T145 → prerequisite lifecycle T146. T147 and T148 run their own acceptance/inner Red before any further production fixes. T149–T151 complete inventory and checkpoint verification.
- US2 increment A: acceptance T152 → inner tests T153/T154/T155 → Domain T156/T157 → Ports T158 → schema T159 → compatibility T160 → persistence T161 → host read/create T162.
- US2 increment B: acceptance T163 → inner tests T164 → orchestration T165 → guarded write T166 → caller/fixture migration T167/T168 → integrity/transaction extensions T169/T170 → inventory/wiring T171/T172 → checkpoints T173/T174.
- An implementation step may introduce declarations needed by the next step, but infrastructure/import failures never establish behavioral Red. Keep schema/host migration internal until the coherent increment is Green; never allow missing-version replacement to succeed during integration.
- Each changed increment records relevant failing behavior before implementation, passing relevant tests afterward and refactoring consideration. Hold source/tests/config stable during a recorded run; do not overlap Red/Green executions for an increment. Consolidation is allowed when associations and order remain reviewable.
- Finalization: T175 and T176 are sequential gate-hardening increments. After both, T177/T178 may proceed on disjoint documentation. T179 waits for all changes; T180 refreshes the review without changing implementation; T181 validates the assembled evidence. Any later implementation change invalidates the final run.

### Parallel Opportunities

| Tasks | Earliest start | Why safe |
|---|---|---|
| T139, T140, T141 | After T138 acceptance Red | Separate Application, Repository and Domain test files |
| T153, T154, T155 | After T152 acceptance Red | Separate Domain, adapter and Application test files |
| T177, T178 | After T176 | Separate documentation and review artifacts |

Repository/model/cleanup implementation and cross-story fixture migrations remain serial. Parallel authoring pauses during state-associated evidence runs. `[P]` never overrides these prerequisites or permits same-file edits.

## Parallel Example: User Story 1

After T138 has recorded acceptance Red, author these tasks together, then record their relevant inner failures on a stable tree:

```text
T139: tests/application/test_enrollment_flow.py, test_conflict.py, test_failure_outcomes.py
T140: tests/adapters/test_repository_lifecycle.py
T141: tests/domain/test_values.py, test_records.py
```

Implement T142–T146 sequentially; retain acceptance and inner Green before the T151 checkpoint.

## Parallel Example: User Story 2

After T152 acceptance Red, author these tasks together, then record inner failures before T156:

```text
T153: tests/domain/test_student_values.py, test_policies.py, test_records.py
T154: tests/adapters/test_student_uow.py, test_sqlite.py
T155: tests/application/test_student_details.py
```

After T162, execute T163 acceptance Red first, then author and execute T164 inner Red, and implement T165/T166 serially. Do not run T167's caller migration concurrently with T163/T164 edits.

## Implementation Strategy

### MVP First (User Story 1)

1. Complete Setup and Foundation; preserve historical proof and make new required evidence explicit.
2. Complete US1 through T151 and demonstrate all 19 enrollment families at HTTP plus real Repository contracts. This is the suggested enrollment MVP scope.
3. Validate the enrollment increment independently. Full versioned-host delivery and v3.0.0 certification still require US2 and all final gates.

### Incremental Delivery

1. US1 moves complete enrollment construction behind Repository, proves actual identity confirmation, rollback and commit exposure, and preserves GraphQL/FR-009/FR-014 behavior.
2. US2 increment A adds shared versioned schema, typed snapshots, Repository Student creation and trusted reads.
3. US2 increment B delivers required expected versions, guarded full replacement and deliberate reload/retry; complete the coherent migration before releasing the changed host contract.
4. T174 validates both boundaries together. Polish restricts production Entity call sites, enforces exact inventories, reviews semantics and validates fresh final evidence.

### Parallel Team Strategy

The parallel groups above are scheduling options, not instructions to launch agents. If multiple contributors implement this plan, coordinate test authoring on disjoint files, keep shared production modules with one owner, and pause edits during recorded runs. Both story implementations remain sequential because they share persistence and contracts.

## Requirement and Contract Coverage

| Requirement / contract | Owning tasks |
|---|---|
| FR-001–FR-010; SC-001–SC-004; enrollment-api.md and unchanged schema.graphqls | T138–T151, T168, T174, T179 |
| FR-014 / US1 19 and mixed invalid-course precedence | T138, T139, T144, T150 |
| FR-015–FR-017; SC-008–SC-010; domain-construction.md and repository-lifecycle.md | T138–T148, T152–T162, T169–T170, T175, T178 |
| FR-011–FR-013; SC-005–SC-007; Unicode semantics and existing Student variants | T153, T157, T160–T162, T165–T171, T174 |
| FR-018; US2 14–17; SC-011; student-details.md and versioned data-model.md | T152–T174 |
| Constitutional Outside-In chronology, new increment/history distinction | T130–T136, T138–T140, T147, T152–T155, T163–T164, T173, T176, T178–T181 |
| Architecture, real Repository contracts, whole-Core coverage and evidence-based completion | T140–T146, T154, T169–T170, T174–T181 |

## Notes

- Open scope is 52 tasks: Setup 3, Foundation 5, US1 14, US2 23, Polish 7. Eight tasks carry `[P]` within the dependency groups above.
- Historical completed tasks are archived intact, not reopened or counted as remaining work. Existing evidence bytes must remain unchanged except the explicitly archived/replaced active final/review outputs during implementation.
- Domain owns business rules; Application sequences policy and transactions; persistence confirms identity, invokes Domain lifecycle APIs and translates technical representations. No Entity lifetime tracking, reservation protocol, generated identity Port or redundant layering DTO is planned.
- Passing tests or a green old manifest cannot prove new TDD chronology, semantic boundary isolation or final v3.0.0 compliance. Only T181 can conclude implementation completion after every applicable mandatory check passes.
