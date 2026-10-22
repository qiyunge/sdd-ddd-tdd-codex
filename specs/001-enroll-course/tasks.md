---
description: "Task list for the Student Self-Enrollment constitution v2.3.1 migration"
---

# Tasks: Student Self-Enrollment

**Input**: Design documents from `/specs/001-enroll-course/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Included. Constitution v2.3.1 and the specification require acceptance-guided Outside-In TDD for new or changed behavior. A missing import or signature is not behavioral Red. Behavior that already passes is recorded as verification. Do not manufacture a failing run for it.

**Organization**: Remaining migration only. Historical tasks T001–T100, the C1/T050 reassessment, and the Unicode verification stay in git history and `specs/001-enroll-course/evidence/`. Do not execute them again and do not rewrite their evidence bytes.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2)
- Every task includes an exact file path

## Path Conventions

- Single project: `src/enrollment/`, `tests/`, `scripts/` at the repository root
- Design and evidence: `specs/001-enroll-course/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Freeze the current tree before the migration. The Python 3.12, Flask, graphql-core, Waitress, and SQLite project already exists. Do not upgrade dependencies or recreate it.

- [ ] T101 Record the current `digest()` of `src/`, `tests/`, `scripts/`, `pyproject.toml`, and `uv.lock` in `specs/001-enroll-course/evidence/reconciliation/alignment-baseline.json`, and copy `specs/001-enroll-course/evidence/final/` byte-for-byte into `specs/001-enroll-course/evidence/history/pre-v231-alignment/` with a SHA-256 index
- [ ] T102 Document the bootstrap capture fields (implementation-state digest, start and finish times, command, test identity, acceptance-versus-inner role) in `specs/001-enroll-course/evidence/README.md`, and run the existing HTTP and host acceptance suites as verification baselines

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Evidence chronology and shared persisted-state types that both stories use

**⚠️ CRITICAL**: No user story work begins until this phase is complete

- [ ] T103 Add failing behavioral tests in `tests/architecture/test_quality_gates.py` for a consolidated evidence record that carries implementation-state digest, execution order, test identity, and acceptance-versus-inner role, and for rejection of a missing or defaulted state, an unrelated test, reversed order, a tree that changes during the run, a failing Green, and stale final evidence
- [ ] T104 Extend `scripts/record.py` so each new record stores that digest, test identity, and acceptance-versus-inner role while keeping lowercase `red`, `green`, `refactor`, and `verification` stages and the positional command form
- [ ] T105 Update `scripts/check_evidence.py` and `scripts/assemble_evidence.py` so new records must carry those associations, a valid consolidated record passes, and historical output-only files remain byte-for-byte without counting as v2.3.1 proof
- [ ] T106 Add `InvalidPersistedState` in `src/enrollment/domain/outcomes.py` and `DataIntegrityFailure` as a `StorageFailure` category in `src/enrollment/application/contracts.py`
- [ ] T107 Add failing reconstitution tests in `tests/domain/test_values.py` and `tests/domain/test_student_values.py`: an empty or non-text stored identifier, and a missing, empty, or whitespace-only stored name or email (including a non-breaking space), return `InvalidPersistedState` rather than `InvalidIdentifier` or `InvalidStudentDetails`; a stored value that contains a non-whitespace character is restored with its original spelling
- [ ] T108 Implement `.reconstitute(raw)` for identifiers, `StudentName`, and `StudentEmail` in `src/enrollment/domain/values.py`, keeping raw `.create` results unchanged: identifiers are nonempty opaque strings compared exactly, with no trimming or case folding; name and email are actual strings containing a non-whitespace character, with original text retained

**Checkpoint**: Evidence tooling accepts a real consolidated record and rejects a record with no implementation state. Value reconstitution distinguishes invalid stored text from invalid input.

---

## Phase 3: User Story 1 - Student Self-Enrollment (Priority: P1) 🎯 MVP

**Goal**: Enrollment keeps FR-009 order and the public GraphQL contract, and persisted enrollment state is restored through controlled reconstitution

**Independent Test**: HTTP POST `/graphql` with Flask’s test client, real graphql-core execution, credential headers, an injected verifier, and file-backed SQLite. The fifteen enrollment scenarios pass, and FR-014 unusable identities return `INVALID_REQUEST` with no record disclosure.

### Tests for User Story 1 ⚠️

> Write these tests first. They must fail for the expected behavioral reason before T112.

- [ ] T109 [P] [US1] Add HTTP acceptance in `tests/acceptance/test_enrollment.py` for FR-014: after a verified acting identity, a missing or empty target student identity returns `INVALID_REQUEST` before ownership, with no student, programme, course, or enrollment disclosure; after ownership, a missing or empty course identity returns `INVALID_REQUEST` before the missing-course check. Keep the existing fifteen scenario identities. Non-text values that fail GraphQL schema validation stay protocol errors
- [ ] T110 [P] [US1] Add application tests in `tests/application/test_identity.py` and `tests/application/test_enrollment_flow.py` that a non-text student or course identity returns `INVALID_REQUEST` at the same points, and that a second pair conflict whose re-evaluation still cannot observe the saved enrollment returns `PERSISTENCE_FAILURE` without deleting the saved row
- [ ] T111 [P] [US1] Add persistence tests in `tests/adapters/test_sqlite.py`: a corrupt stored enrollment or identifier becomes `DataIntegrityFailure` and sanitized `PERSISTENCE_FAILURE`; a valid enrollment restores after its course is no longer offered; a missing row stays `None`; a stored student whose name or email is missing, empty, or whitespace-only, including a non-breaking space, becomes `DataIntegrityFailure` when enrollment loads that student; a valid stored student restores with its original spelling and a dangling programme reference remains representable

### Implementation for User Story 1

- [ ] T112 [US1] Add typed `.create` and `.reconstitute` for `Programme`, `Course`, `ProgrammeCourseOffering`, and `Enrollment`, and add `Student.reconstitute` for `StudentId`, `ProgrammeId`, `StudentName`, and `StudentEmail`, in `src/enrollment/domain/models.py`. Add `VerifiedIdentity.create(SubjectId)` in `src/enrollment/domain/values.py`. Leave `Student.create` parsing raw fields until T118. `Enrollment.create` accepts `StudentId` and `CourseId` only. Reconstitution does not replay current offering eligibility or current email availability. Name and email must be actual strings containing a non-whitespace character, with original text retained. A dangling programme reference must remain representable
- [ ] T113 [US1] Call those factories from `src/enrollment/application/enroll.py` and `src/enrollment/adapters/identity/verifier.py` at the existing decision points. Preserve verification, then student identity, ownership, course identity, Student, Programme, Course, duplicate policy, and offering policy. Compare the subject identifier and the student identity exactly, with no trimming or case folding. One `PairConflict` triggers one full re-evaluation; a second conflict becomes `StorageFailure`
- [ ] T114 [US1] Load persisted Student, Programme, Course, ProgrammeCourseOffering, and Enrollment rows in `src/enrollment/adapters/persistence/sqlite.py` through value `.reconstitute` and then the record `.reconstitute` added in T112, including `Student.reconstitute`. Map `InvalidPersistedState` to `DataIntegrityFailure`. Keep `None` for absence. Keep `BEGIN IMMEDIATE`, the five-second lock timeout, and SQL `COMMIT`/`ROLLBACK` on an autocommit connection
- [ ] T115 [US1] Run the User Story 1 checkpoint with `tests/acceptance/test_enrollment.py`, `tests/acceptance/test_concurrency.py`, `tests/acceptance/test_eligibility_races.py`, `tests/acceptance/test_retry.py`, `tests/adapters/test_server.py`, and `tests/adapters/test_package_resources.py`, and record the passing runs as verification with `scripts/record.py` under `specs/001-enroll-course/evidence/reconciliation/`

**Checkpoint**: User Story 1 is independently testable through POST `/graphql`. The fifteen scenarios and both FR-014 cases pass, and a restored enrollment survives a later offering change.

---

## Phase 4: User Story 2 - Valid Student Details (Priority: P1)

**Goal**: Student create and replace use typed Domain values and first-defect order. Stored students already reconstitute through the API added in T112

**Independent Test**: Call `enrollment.application.student_details.save_student` against real file-backed SQLite. Scenarios `student-details-1` through `student-details-10` pass, including the original twenty-three parameterized cases.

### Tests for User Story 2 ⚠️

> Write these tests first, and only after T115 has been recorded. They must fail for the expected behavioral reason before T118.

- [ ] T116 [P] [US2] Add host acceptance in `tests/acceptance/test_student_details.py` and extend `scripts/acceptance_inventory.py` with `student-details-8` (creating an existing student identity returns the existing-student result and leaves the record unchanged), `student-details-9` (replacing a missing student identity returns the missing-student result and creates no student), and `student-details-10` (several defects return only the first, in the order student identity, programme identity, name, then email). The exact-set check must still require the original twenty-three parameterized cases. Neither existence result is an email conflict
- [ ] T117 [P] [US2] Add tests in `tests/domain/test_student_values.py` and `tests/application/test_student_details.py` that `Student.create` accepts `StudentId`, `ProgrammeId`, `StudentName`, and `StudentEmail`, that an unusable student identity together with a whitespace-only name returns `InvalidIdentifier`, and that a valid identity with an invalid name and another student's email returns `InvalidStudentDetails("name")`

### Implementation for User Story 2

- [ ] T118 [US2] Change `Student.create` in `src/enrollment/domain/models.py` to accept `StudentId`, `ProgrammeId`, `StudentName`, and `StudentEmail`. Keep the `Student.reconstitute` API added in T112. Name and email must be actual strings containing a non-whitespace character, with original text retained. Student equality and hashing use `StudentId` alone. `StudentEmail` equality and hashing use the full `str.casefold()` key of the entire address
- [ ] T119 [US2] Convert raw fields in `src/enrollment/application/student_details.py` through `StudentId`, `ProgrammeId`, `StudentName`, and `StudentEmail` factories in that order, then call typed `Student.create`. Stop at the first defect. Creating an existing identity returns the existing-student result. Replacing a missing identity returns the missing-student result. The enrollment unit of work gains no Student write method
- [ ] T120 [US2] Keep Student-session reads in `src/enrollment/adapters/persistence/sqlite.py` on the `Student.reconstitute` path from T114. Invalid persisted name or email on the host operation becomes `DataIntegrityFailure` and the existing `StudentStorageFailure` result. Keep the unique expression index `students_email_key`, original spelling, significant leading and trailing whitespace, and refusal of an incompatible legacy schema without writes or backfill
- [ ] T121 [US2] Run the User Story 2 checkpoint with `tests/acceptance/test_student_details.py` and `tests/acceptance/test_student_record_integrity.py`, including Unicode expansion (`Straße@example.com` versus `STRASSE@EXAMPLE.COM`) and composition non-equivalence, and record the passing runs as verification with `scripts/record.py` under `specs/001-enroll-course/evidence/reconciliation/`

**Checkpoint**: User Stories 1 and 2 both work. Enrollment still does not create or modify students. Rejected student changes preserve previous details.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Caller enforcement, semantic review, and final evidence against the migrated tree

- [ ] T122 Enforce supported factory and reconstitution use, including imported aliases, in `tests/architecture/test_boundaries.py`, and migrate remaining ordinary callers in `src/enrollment/` and `tests/` off internal constructors. Keep explicit internal-misuse tests. Do not require absolute constructor privacy
- [ ] T123 Record the semantic-boundary review in `specs/001-enroll-course/evidence/reconciliation/review.json`: Domain owns ownership, duplicate, offering, and email-availability decisions; Application owns sequencing and transactions; adapters convert. State that the Import Linter result does not prove those semantics
- [ ] T124 [P] Update `README.md` and `specs/001-enroll-course/evidence/README.md` with the implemented factory, reconstitution, and `scripts/record.py` commands, and state that historical records are not v2.3.1 chronology
- [ ] T125 [P] Write `specs/001-enroll-course/evidence/reconciliation/alignment-history-review.json` preserving C1/T050 and the Unicode-verification bytes, and report every historical record that has no implementation-state association
- [ ] T126 Run `bash scripts/check-quality.sh` on the stable tree and require the fifteen enrollment scenarios, the twenty-three Student cases, `student-details-8` through `student-details-10`, the FR-014 HTTP cases, strict mypy, Ruff, Import Linter, and 100% statement and branch coverage of `src/enrollment/domain` and `src/enrollment/application`
- [ ] T127 Update `specs/001-enroll-course/evidence/reconciliation/review.json` so its digest matches the T126 tree
- [ ] T128 Assemble the manifest with `.venv/bin/python -m scripts.assemble_evidence` into `specs/001-enroll-course/evidence/final/manifest.json`
- [ ] T129 Validate with `.venv/bin/python -m scripts.check_evidence` and require `passed: true` in `specs/001-enroll-course/evidence/final/validation.json`. On failure, fix the owning task and rerun T126–T129

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies. Start immediately.
- **Foundational (Phase 2)**: Depends on Setup. Blocks both user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational. No dependency on User Story 2.
- **User Story 2 (Phase 4)**: Depends on Foundational and starts only after T115 has been recorded. T112 and T114 are already complete by then. `src/enrollment/domain/models.py` and `src/enrollment/adapters/persistence/sqlite.py` stay shared with User Story 1.
- **Polish (Phase 5)**: Depends on T115 and T121.

### User Story Dependencies

- **User Story 1 (P1)**: Starts after T108. Independently testable at POST `/graphql`.
- **User Story 2 (P1)**: Starts after T115 is recorded. Independently testable through `save_student`. It uses `Student.reconstitute` from T112 and changes `Student.create` in T118.

### Within Each User Story

- Behavioral tests are written and fail for the expected reason before implementation.
- Domain factories and reconstitution come before application callers.
- Application callers come before adapter row loading.
- The story checkpoint records verification after the relevant tests pass.

### Parallel Opportunities

- T109, T110, and T111 touch different test files and can run together after T108.
- T116 and T117 touch different test files and can run together only after T115 has been recorded.
- T124 and T125 touch different documents and can run together after T123.
- `src/enrollment/domain/models.py` and `src/enrollment/adapters/persistence/sqlite.py` stay serial across T112, T114, T118, and T120.

---

## Parallel Example: User Story 1

```bash
# After T108, write the three failing User Story 1 test tasks together:
Task: "T109 HTTP FR-014 acceptance in tests/acceptance/test_enrollment.py"
Task: "T110 application identity and conflict tests in tests/application/test_identity.py and tests/application/test_enrollment_flow.py"
Task: "T111 corrupt-row and restoration tests in tests/adapters/test_sqlite.py"

# Then implement serially:
Task: "T112 typed factories and Student.reconstitute in src/enrollment/domain/models.py, and VerifiedIdentity.create in src/enrollment/domain/values.py"
Task: "T113 factory callers in src/enrollment/application/enroll.py and src/enrollment/adapters/identity/verifier.py"
Task: "T114 reconstitution in src/enrollment/adapters/persistence/sqlite.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational.
3. Complete Phase 3: User Story 1 through T115.
4. Stop and validate POST `/graphql` independently.

### Incremental Delivery

1. Setup and Foundational make evidence and value reconstitution available.
2. User Story 1 delivers restored enrollment, `Student.reconstitute`, and FR-014 at the public HTTP boundary. Record T115 before any User Story 2 edit.
3. User Story 2 delivers typed `Student.create`, scenarios 8–10, and host-path stored-detail integrity.
4. Polish enforces callers, reviews semantics, and runs the final quality and evidence gates.

### Parallel Team Strategy

1. One sequence completes T101–T108.
2. After T108, one person can write T109–T111 together.
3. Finish T115 and record it with `scripts/record.py` before anyone starts T116 or T117. After that record exists, T116 and T117 can be written together.
4. T118–T120 stay with one owner. T124 and T125 can proceed together after T123.

---

## Notes

- Active work is T101–T129. Historical T001–T100 are not open tasks.
- [P] means different files and no unfinished dependency.
- [US1] and [US2] are the only story labels. Setup, Foundational, and Polish have none.
- Commit after each completed task or logical group.
- A missing, failed, skipped, blocked, or stale mandatory gate blocks a completion claim.
- T129 is the first point at which Constitution v2.3.1 implementation compliance may be claimed.
