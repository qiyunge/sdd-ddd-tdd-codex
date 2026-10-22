# Implementation Plan: Student Self-Enrollment

**Branch**: `001-enroll-course` | **Date**: 2026-10-22 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-enroll-course/spec.md`

**Governance**: Constitution v2.3.1 is effective (ratified 2026-10-21, amended 2026-10-22). This plan complies with it and does not amend it. Enrollment eligibility, FR-009 precedence, and student-detail validity stay as specified. Historical C1/T050 and Unicode-verification records remain historical. They are not proof of v2.3.1 compliance, and this plan does not manufacture missing chronology.

## Summary

Preserve the implemented enrollment and Student-detail behavior, public GraphQL contract, dependencies, and quality gates. Finish the constitution migration that source inspection still shows as open: typed Entity factories, controlled reconstitution, persisted-state integrity classification, caller migration, acceptance coverage for FR-014 and User Story 2 scenarios 8–10, and state-associated TDD evidence.

Feature-specific decisions are recorded in this plan. `.specify/memory/architecture-decisions.md` is not present; this plan does not depend on it.

## Technical Context

**Language/Version**: Python 3.12 (`>=3.12,<3.13`)

**Primary Dependencies**: Flask `>=3.1,<3.2` (HTTP), graphql-core `>=3.3,<3.4` (SDL-first GraphQL), Waitress `>=3,<4` (WSGI). Development: pytest, httpx, coverage.py, strict mypy, Ruff, Import Linter. Locked in `uv.lock`.

**Storage**: File-backed SQLite through the standard library `sqlite3`. Five persisted record types. No ORM. Worker-owned connections.

**Testing**: pytest. Enrollment acceptance uses Flask’s test client, real temporary SQLite, and an injected identity verifier. Student-detail acceptance calls the internal host operation against real SQLite. Architecture tests, port spies, a real Waitress socket, and an installed-wheel check remain mandatory.

**Target Platform**: Linux. One process; Waitress worker threads; one SQLite connection per operation.

**Project Type**: HTTP GraphQL service plus one internal trusted Python host operation for Student create/replace.

**Performance Goals**: No throughput or latency target. A SQLite lock wait longer than five seconds is a technical failure.

**Constraints**: Keep `pyproject.toml` and `uv.lock` without dependency upgrades. No new public API, eligibility rule, deployment topology, or performance promise. Identity-provider calls stay outside the write transaction.

**Scale/Scope**: Single local database. Fifteen enrollment acceptance scenarios, the existing twenty-three parameterized Student-detail cases, and three additional host-acceptance identities for User Story 2 scenarios 8–10.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

**Pre-design result: PASS.** No waiver is requested. No technical choice remains marked for clarification. The stack, transaction boundary, and failure vocabulary are already fixed by the specification and the current codebase. Remaining work is migration and evidence, specified below, and does not relax a principle.

| Principle | Design disposition |
|---|---|
| I. Hexagonal Architecture and inward dependencies | Application owns use-case orchestration and ports. Domain owns business decisions. Adapters translate boundaries and may call supported Domain factories and reconstitution directly. Application is not a mandatory gateway for that adaptation. Core stays free of Flask, Werkzeug, graphql-core, sqlite3, Waitress, and httpx. |
| II. Domain ownership and boundary contracts | Every Value Object and Entity exposes `.create`. Entity factories accept validated Domain Types. Reconstitution is a separate API. Expected failures are explicit results. Invalid persisted state is a data-integrity failure. See [Domain construction](contracts/domain-construction.md). |
| III. Outside-In TDD | Public boundaries and evidence rules are declared under [Evidence capture](#evidence-capture). Cohesive behavioral increments. Historical records stay unmodified. |
| IV. Architecture and coverage | Structural checks and semantic checks are separate. Coverage scope is declared under [Coverage scope](#coverage-scope). The project gate is stricter than the constitutional branch floor. |
| V. Evidence-based completion | Final quality, assembly, and evidence validation run against the final implementation state. A design pass is not a completion claim. |

## Project Structure

### Documentation (this feature)

```text
specs/001-enroll-course/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── domain-construction.md
│   ├── enrollment-api.md
│   ├── schema.graphqls
│   └── student-details.md
├── tasks.md             # reassessment belongs to speckit-tasks
└── evidence/
```

### Source Code (repository root)

```text
src/enrollment/
  domain/{values,models,policies,outcomes}.py
  application/{enroll,student_details,contracts,ports,student_ports,student_contracts,cleanup}.py
  adapters/{graphql,http,persistence,identity}/
  bootstrap.py
tests/{acceptance,domain,application,adapters,architecture}/
scripts/{record,assemble_evidence,check_evidence,check_quality,acceptance_inventory}.py
```

**Structure Decision**: Extend these modules. Bootstrap is the composition root and may depend on adapters. The HTTP adapter may call the GraphQL execution adapter. Identity, persistence, and GraphQL adapters stay independent of one another. Domain imports neither Application nor adapters.

## Feature decisions

### Ports and adapter adaptation

Application owns `IdentityVerifier`, the enrollment unit of work, and the separate Student unit of work. Domain does not import those ports.

Adapters may parse external representations and call supported Domain factories or reconstitution while implementing a port. That call is technical adaptation. Adapters do not sequence FR-009, compare ownership, decide duplicates, decide offerings, or decide email availability. Application uses Domain types directly. No DTO is added solely to separate Application from Domain.

### Factories

| Model | `.create` inputs | Expected failure |
|---|---|---|
| StudentId, ProgrammeId, CourseId, SubjectId | raw value | `InvalidIdentifier` when the value is missing, empty, or not text |
| StudentName, StudentEmail | raw value | `InvalidStudentDetails(field)` when missing, empty, or whitespace-only, including Unicode whitespace |
| VerifiedIdentity | validated `SubjectId`, only after trusted verification | none for a validated subject; no Student-existence claim |
| Student | `StudentId`, `ProgrammeId`, `StudentName`, `StudentEmail` | typed components only; no programme lookup and no email-availability lookup |
| Programme, Course | the matching identifier | factory required with no extra invariant |
| ProgrammeCourseOffering | `ProgrammeId`, `CourseId` | both typed identifiers |
| Enrollment | `StudentId`, `CourseId` | typed pair; reached only after duplicate and offering policies pass |

Value-object factories accept raw representations and return the value or an explicit validation failure. Entity factories accept validated Domain Types and enforce entity invariants. `Programme`, `Course`, and `ProgrammeCourseOffering` still have factories. Internal constructors may exist and may raise on misuse. They are not a supported creation API. Absolute constructor privacy is not required. Architecture tests enforce supported API use, including aliases.

`InvalidIdentifier` stays fieldless. First-defect order is observable by pairing an earlier defect with a later one: an unusable student identity together with a whitespace-only name returns `InvalidIdentifier`, and a valid identity with an invalid name and a conflicting email returns `InvalidStudentDetails("name")`.

### Reconstitution and integrity

Persisted values expose `.reconstitute(raw)`. Persisted records expose `.reconstitute` on validated components. Both enforce persisted-state invariants and return `InvalidPersistedState` when those invariants fail. Reconstitution does not replay current offering eligibility or contextual email availability. A valid historical enrollment remains restorable after the course is no longer offered. A Student remains restorable when another student would now conflict on email; the unique index still governs new writes.

Persistence adapters call reconstitution directly. `InvalidPersistedState` maps to Application `DataIntegrityFailure`, a `StorageFailure` category, and then the existing sanitized `PERSISTENCE_FAILURE` or `StudentStorageFailure`. It is not absence, `INVALID_REQUEST`, invalid details, an email conflict, or a new FR-009 reason. Unexpected programming errors propagate to the outer error boundary.

### Transaction coordination

Use a fresh SQLite connection per operation with Python 3.12 `autocommit=True`, a five-second timeout, SQL `BEGIN IMMEDIATE` before prerequisite reads, and SQL `COMMIT` or `ROLLBACK`. Close the connection in the same worker. `connection.commit()` and `connection.rollback()` are not substitutes in autocommit mode. Flask teardown does not complete the transaction. No network call runs inside the transaction.

Enrollment port writes return `Added | PairConflict`. A `PairConflict` rolls back and runs one fresh full ordered attempt. A second conflict, including one whose re-evaluation still cannot observe the saved enrollment, becomes technical `StorageFailure` and public `PERSISTENCE_FAILURE`. It is not reported as already enrolled and does not delete the saved row. Only the enrollment-pair unique constraint maps to `PairConflict`.

Student port writes return `Saved | EmailKeyConflict`. Only the `students_email_key` unique failure maps to `EmailKeyConflict`, then to the email-conflict result. Other driver errors stay technical.

## Architecture and enrollment flow

Domain owns ownership comparison, duplicate policy, offering eligibility, email availability, and invariants. Application owns verifier invocation, repository absence, exact FR-009 sequencing, and transaction orchestration. Application may branch on a Domain outcome. It does not recompute the predicate.

Ordered enrollment handling:

1. Verify the credential. Negative verification returns generic `DENIED` before ownership and persistence. Provider outage is `IDENTITY_UNAVAILABLE`, also before persistence.
2. Validate the target student identity. An unusable value (missing, empty, or not text) is `INVALID_REQUEST` before ownership, with no student, programme, course, or enrollment disclosure (FR-014). This is not an FR-009 reason and not a generic denial.
3. Apply Domain ownership to `VerifiedIdentity` and the target `StudentId`. The subject identifier and the student identity are compared exactly, with no trimming or case folding. A mismatch returns the same generic `DENIED`.
4. Validate `CourseId`. An unusable course identity is `INVALID_REQUEST` before the missing-course check (FR-014).
5. Inside the immediate transaction, load Student, Programme, and Course in that order. Application returns the matching missing-record outcome and stops. A missing programme is not “course not offered.”
6. Invoke Domain duplicate policy, then Domain offering policy. Stop at the first rejection.
7. Create `Enrollment` through its factory, add, commit, then report success.

Enrollment does not create or modify students, programmes, courses, memberships, or offerings (FR-010).

## Student details and data integrity

`name` and `email` are required text. Each must contain a non-whitespace character under Python `str.strip`, so tabs, line breaks, and non-breaking spaces are rejected. The supplied spelling is stored. Email equality and hashing use the full `str.casefold()` key, including expansions such as `ß` to `ss`. Leading and trailing whitespace on a nonblank value remains significant. Unicode composition forms are not equated. No syntax check, trimming, or provider alias rule is added. Student equality and hashing use `StudentId` alone.

The host operation validates student identity, programme identity, name, then email, and stops at the first defect. It then distinguishes create-of-existing (`StudentAlreadyExists`) from replace-of-missing (`StudentNotFound`) before the email-availability policy. Neither existence result is an email conflict. Programme existence is not required. The enrollment unit of work gains no Student write methods.

SQL functions backed by Domain predicates are registered on every persistence connection. The unique expression index is `students_email_key`. A connection without those functions fails closed. Compatible initialization is idempotent. An incompatible legacy schema is refused without writes or backfill.

## Remaining migration

Inspected against current source on 2026-10-22. Behavior that already matches the specification stays in place.

| Location | Required change |
|---|---|
| `domain/outcomes.py`, `application/contracts.py` | Add `InvalidPersistedState` and `DataIntegrityFailure(StorageFailure)` |
| `domain/values.py` | Add `VerifiedIdentity.create(SubjectId)` and `.reconstitute` for identifiers and required text. Keep raw `.create` results |
| `domain/models.py` | Typed factories for Student, Programme, Course, ProgrammeCourseOffering, and Enrollment. Separate `.reconstitute` for each persisted record. Stop parsing raw scalars inside `Student.create` and `Enrollment.create` |
| `application/student_details.py` | Convert raw fields through value-object factories in spec order, then call typed `Student.create` |
| `application/enroll.py`, identity adapter | Replace direct `Enrollment` and `VerifiedIdentity` construction with supported factories at the current decision points |
| `adapters/persistence/sqlite.py` | Reconstitute values, then records. Map `InvalidPersistedState` to `DataIntegrityFailure`. Keep `None` for absence |
| Tests and fixtures | Ordinary callers use factories or reconstitution. Add inventory checks, alias checks, restoration tests, FR-014 HTTP cases, and User Story 2 scenarios 8–10 |
| `scripts/record.py`, `scripts/check_evidence.py` | Associate runs with implementation state, test identity, and acceptance-versus-inner role. `digest()` exists and is not yet stored. `validate_runs` currently checks AssertionError Red before Green only |

## Verification and TDD evidence

### Evidence capture

Acceptance boundaries:

- Enrollment: HTTP POST `/graphql` through Flask’s test client, real graphql-core execution, credential headers, an injected verifier, and file-backed SQLite. Waitress covers sockets and worker scheduling on a local ephemeral port.
- Student details: the host operation `enrollment.application.student_details.save_student` against real SQLite. It is not an HTTP route.

Each new or changed behavior uses a cohesive increment: a relevant behavioral test fails for the expected reason, implementation makes the relevant tests pass, and refactoring is considered with those tests still passing. Shared tests may cross layers. Import, signature, and configuration failures are not behavioral Red. Passing behavior is recorded as verification. Do not invent a failing run for it.

The recorder keeps lowercase `red`, `green`, `refactor`, and `verification` stages and the positional command form. Each new record stores the command, output, exit code, start and finish times, the `digest()` of `src`, `tests`, `scripts`, `pyproject.toml`, and `uv.lock`, the increment and test identity, and whether the activity is acceptance-first or inner-layer. Consolidated records are valid when that chronology stays reviewable. The validator rejects a missing or defaulted state, an unrelated test, a missing role, reversed or overlapping order, a tree that changes during the run, a failing Green, and stale final evidence. Historical files are preserved byte for byte. Where they lack state or role, the review says so.

### Architecture fitness

Import Linter enforces inward layers, the Core framework ban, outbound-adapter independence, a Flask-free GraphQL adapter, and an HTTP adapter that does not import identity or persistence. Focused tests cover public annotations, dynamic imports, supported factory usage, and direct adapter reconstitution, with allowed and violating fixtures.

Behavioral tests and an explicit review cover conversion semantics, error classification, and which layer owns each decision. A passing import graph is not that proof. The review names the two kinds of evidence separately.

### Coverage scope

Tooling is coverage.py with `branch = true` and `fail_under = 100`. Source scope is `src/enrollment/domain` and `src/enrollment/application`, including unimported modules. That complete-Core statement-and-branch gate includes every branch of each affected business function, which satisfies the constitutional whole-function branch minimum.

Justified exclusion: coverage’s default omission of a function body that is only `...` is accepted only for a module whose contents are `Protocol` method signatures and imports. `scripts/check_evidence.py` already checks that shape. No business-logic function is excluded. A branchless function still needs a behavioral test. No changed-lines gate and no `pragma: no cover` on business logic.

Preserve strict mypy, Ruff lint and format, architecture tests, contract tests, the fifteen enrollment scenarios, and the Student-detail inventory below.

## Delivery and completion

1. Reassess `tasks.md` from this plan. Keep C1/T050 and the Unicode-verification history. Do not execute completed behavior again.
2. Extend evidence capture and the validator, with tests for a valid consolidated record and for invalid or missing associations, before any new chronology claim.
3. Migrate factories, reconstitution, callers, and integrity mapping in acceptance-guided increments. Extend structural and behavioral architecture checks.
4. Add host acceptance identities `student-details-8`, `student-details-9`, and `student-details-10` for existing-student create, missing-student replace, and first-defect order. Extend `STUDENT_CASES` so the exact-set check includes them and still fails if one of the original twenty-three cases is missing.
5. Add HTTP acceptance for FR-014: unusable student identity after verification, and unusable course identity after ownership. Both return `INVALID_REQUEST` with no record disclosure. Keep the fifteen scenario identities.
6. Run the final checks below on the stable tree. Re-run after any source, test, or config change.

```bash
bash scripts/check-quality.sh
# Review raw results and update evidence/reconciliation/review.json.
.venv/bin/python -m scripts.assemble_evidence
.venv/bin/python -m scripts.check_evidence
```

Any missing, failed, skipped, blocked, or stale mandatory gate prevents a completion claim. This planning revision changes design documents only.

**Next workflow:** `$speckit-tasks`.

## Constitution Check — Post-Design

**Post-design result: PASS.** Research, the data model, and the contracts resolve the technical context without an open clarification. They specify transaction coordination, boundary conversions, acceptance boundaries, factory and reconstitution contracts, creation-only rules that reconstitution does not replay, invalid persisted-state outcomes, coverage scope, and the one justified exclusion. No principle is waived. Implementation of the migration and fresh v2.3.1 evidence remain outstanding; this gate does not certify them.

| Artifact | Constitutional coverage |
|---|---|
| [research.md](research.md) | Stack, transaction, failure, and evidence decisions, including the v2.3.1 reassessment |
| [data-model.md](data-model.md) | Entities, invariants, lifecycle, and restoration rules |
| [contracts/](contracts/) | GraphQL boundary, host Student boundary, and Domain construction |
| [quickstart.md](quickstart.md) | Runnable validation for the specified scenarios and final gates |

## Complexity Tracking

No constitutional violation requires a justification. No additional service or infrastructure is introduced.
