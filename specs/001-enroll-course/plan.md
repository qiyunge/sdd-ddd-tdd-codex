# Implementation Plan: Student Self-Enrollment

**Branch**: `001-enroll-course` | **Date**: 2026-10-22 | **Spec**: [spec.md](spec.md)

**Input**: Current feature specification, FR-001–FR-018 and SC-001–SC-011.

**Governance**: [Constitution v3.0.0](../../.specify/memory/constitution.md) is effective. This plan implements its Repository-controlled Entity lifecycle and the approved rejection of outdated Student replacements. It does not amend the constitution or claim implementation compliance.

## Summary

Retain the Python/GraphQL/SQLite service and its enrollment rules. Move production complete-Entity construction and restoration behind Core-owned Repository Ports, confirm natural/composite identities through uncommitted business-table INSERTs before construction, and keep new Entities inside the creation operation until commit is confirmed. Keep Application in charge of use-case orchestration and commit.

Add saved-version retrieval and conditional full Student replacement to the trusted host integration. An outdated replacement is rejected before email availability is evaluated; it never silently reloads or overwrites newer details. Student identity, Unicode email comparison, and the public GraphQL schema remain unchanged.

Revised [ADR-0001](adr/0001-entity-lifecycle-and-student-revisions.md) removes identity reservations and Entity lifetime handles while preserving Repository-controlled construction and conditional replacement. [Research](research.md#flagged-uncertainties-and-amendments) records the unclear points and their amendments.

## Technical Context

**Language/Version**: Python 3.12 (`>=3.12,<3.13`), existing locked environment.

**Primary Dependencies**: Flask `>=3.1,<3.2`, graphql-core `>=3.3,<3.4`, Waitress `>=3,<4`; pytest, HTTPX, coverage.py, mypy, Ruff, Import Linter. Preserve `pyproject.toml` and `uv.lock`; no dependency upgrade.

**Storage**: Local file-backed SQLite; five business record tables and a Student saved-version column. No ORM, surrogate business identities, external database, or durable pending-entity state.

**Testing**: Enrollment acceptance through Flask HTTP/JSON/GraphQL with an injected verifier and real temporary SQLite; trusted host acceptance through Python read/save operations and real SQLite. Pure Domain tests, Application port doubles, real Repository contract tests, architecture tests, an installed-wheel test, and Waitress socket/concurrency tests complement acceptance.

**Target Platform**: Linux; one process with Waitress threads. Each worker owns its connections from creation to close.

**Project Type**: GraphQL HTTP service and trusted Python Student integration; no management web endpoint.

**Performance Goals**: No new latency, throughput, or availability promise. Preserve the five-second SQLite lock timeout and report timeout as a technical failure.

**Constraints**: `BEGIN IMMEDIATE` before use-case reads, explicit SQL `COMMIT`/`ROLLBACK` with Python 3.12 `autocommit=True`; identity-provider calls occur before transactions. Preserve FR-009, FR-014, full Unicode case folding, exact identifiers, existing schema/transport reason vocabulary, and historical evidence. Conditional replacement intentionally changes the trusted host command/result contract.

**Scale/Scope**: One local database; all 19 US1 and 17 US2 scenario families, every existing parameter variant, and repository/lifecycle fault cases. No multi-host/shared-filesystem deployment, version-history service, student deletion, bulk migration, or background retry.

## Constitution Check

*GATE: Pass before Phase 0 research and re-evaluate after Phase 1 design.*

**Pre-design result: PASS for design feasibility.** The current implementation has v3.0.0/FR-018 gaps; these are migration work, not waivers or completed behavior.

| Principle | Required design and verification |
|---|---|
| I. Inward dependencies | Application defines the Repository and Unit of Work Ports required by its use cases. Persistence adapters implement these Ports. Domain remains independent of Application, Repository, Unit of Work, and infrastructure. Only Repository implementations construct/restore complete production Entities. Value Object factories remain available for boundary conversion. Domain has no persistence/transport imports or I/O. |
| II. Integrity and lifecycle | INSERT the natural/composite identity before `Entity.create`; restore from persisted identities through `Entity.reconstitute`. Domain owns invariants; Repository owns confirmation and SQL. Failure rolls back uncommitted state; pending Entities never leave the creation operation as successful or reusable canceled results. Repository never commits a subset of a use case. |
| III. Outside-In TDD | Acceptance-guided cohesive Red → Green → Refactor increments, real behavioral Red, state-associated chronology, and separate acceptance/inner activity. Existing passing behavior is verification, not invented Red. |
| IV. Architecture and coverage | Enforce production construction call sites and test real INSERT/rollback/commit behavior. Retain complete Domain/Application 100% statement-and-branch coverage, static gates, and explicit semantic boundary review. |
| V. Completion evidence | Mandatory final checks, exact scenario inventory, current review, assembly, and evidence validation must match the final implementation. Historical records remain historical. |

## Project Structure

### Documentation (this feature)

```text
specs/001-enroll-course/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── adr/0001-entity-lifecycle-and-student-revisions.md
├── contracts/
│   ├── domain-construction.md
│   ├── repository-lifecycle.md
│   ├── enrollment-api.md
│   ├── student-details.md
│   └── schema.graphqls
├── tasks.md                       # reassess with speckit-tasks, not this command
└── evidence/                      # preserve historical execution records
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

**Structure Decision**: Extend existing modules without an identity reservation table or Entity transaction tracking. `StudentSnapshot` carries a Student plus saved-version metadata for concurrency; this wrapper has a semantic purpose and is not a redundant layering DTO. Bootstrap remains the composition root; outbound adapters remain independent.

## Feature decisions

### Repository Ports and responsibilities

Application retains identity verification, FR-009 sequencing, absent-record outcomes, Domain policy calls, and the enclosing transaction. It passes validated values or creation/replacement requests, never a newly constructed complete Entity, to Repository methods.

The existing enrollment UoW's read methods are Repository entry points. Replace `add(Enrollment)` with `create_enrollment(StudentId, CourseId) -> Enrollment | PairConflict | applicable Domain creation rejection`. Keep prerequisite reads and no Student write method. The Student UoW exposes `snapshot(StudentId)`, `email_owner(key)`, `create_student(validated details)`, and `replace_student(validated details, expected_version)`; it returns typed snapshots/outcomes. Exact signatures and error ownership are in [repository lifecycle](contracts/repository-lifecycle.md).

### Identity confirmation and creation

Application validates input and invokes Repository through Core-owned Ports. Repository begins or joins the enclosing transaction; the existing UoW executes `BEGIN IMMEDIATE` before use-case reads. Repository performs an ordinary INSERT into the actual business table and obtains the confirmed natural/composite identity from the inserted state. Existing primary-key/unique constraints reject duplicate identities. Do not use INSERT OR REPLACE, ignore a failed insertion, or treat ID syntax as confirmation.

Repository then invokes `Entity.create()` with validated Domain values and the confirmed identity. The inserted row remains uncommitted intermediate persistence state until Domain accepts it. Creation rules execute before any successful commit; SQL constraints/defaults never substitute for Domain decisions. Explicit rejection, persistence failure or unexpected exception rolls back the entire operation's uncommitted changes. Repository never commits independently.

New Entities and pending snapshots remain within the creation operation until the enclosing commit is confirmed. Do not expose them through callbacks, caches, exception payloads or other external effects. Discard pending references on failure so canceled Entities are unavailable for further business use. Domain Entities carry no transaction status or lifecycle handle. No dedicated reservation table, CreationData, ID generator Port or replacement lifecycle abstraction is introduced. Trusted provisioning/test setup uses the same Repository ordering without adding management APIs.

### Restoration

Repository reads actual persisted identity/state, decodes Value Objects through their shared validated `.create` factories, then calls `Entity.reconstitute`. Value Object input validation and persisted-state invariants coincide here, so no separate Value Object restoration factory is needed. Persistence translates invalid Value Object outcomes into `DataIntegrityFailure(StorageFailure)`. Student restoration validates stored saved_version even when enrollment reads return only Student; enrollment adds no version comparison/advancement. Corrupt stored values retain the existing sanitized completion failure. Missing rows remain None.

Restoration never replays current offering eligibility or email availability; a usable programme ID does not imply programme existence. Domain factories accept no transaction handles and perform no persistence I/O. Isolated Domain tests may supply valid identities without persistence; they verify rules, not persistence confirmation.

### Transactions and failures

A fresh worker-owned connection uses Python 3.12 `autocommit=True`, five-second timeout, registered Domain-backed text/email SQL functions, and explicit SQL `BEGIN IMMEDIATE`. Repository methods use the surrounding UoW and never issue `COMMIT`. Application commits once after the entire use case succeeds and returns an Entity or StudentSnapshot only after confirmation. Read-only host snapshot retrieval also closes its read transaction before returning a detached committed snapshot.

On explicit rejection or exception, discard pending creation results and roll back the whole known active, uncommitted UoW. Cleanup preserves an already-propagating primary exception and records secondary faults. If an expected result is pending and rollback/close raises, surface Core StorageFailure/completion failure instead of the ordinary result and retain its context diagnostically. Unconfirmed transaction termination must be reported honestly; pending Entities must remain unavailable for later business use. A failed close after a confirmed commit cannot compensate/delete the committed record. If commit is uncertain, return a technical completion failure requiring reconciliation and discard unpublished results. Do not infer success or assume rollback/deletion is safe. Roll back only a transaction known to remain active and uncommitted; never delete/revert potentially committed complete rows or silently replay a Student update. A later independent read/operational check reconciles current committed state.

Only the precise enrollment-pair uniqueness violation maps to `PairConflict`. It rolls back and allows one new full ordered enrollment attempt. A second unresolved pair conflict becomes `PERSISTENCE_FAILURE`. Only the exact email-key uniqueness violation maps to `EmailKeyConflict`; unrelated constraints remain technical failures.

### Saved versions and conditional replacement

Use a Domain `SavedVersion` Value Object containing a strict integer in 1..9,223,372,036,854,775,807 (booleans/coercion rejected). This is the version representation contract aligned to SQLite's positive signed-64 range; overflow is a technical persistence failure without changes, never wraparound. Store `students.saved_version`; creation establishes 1, and each committed replacement advances it by exactly 1, including identical details. Versions do not change StudentId-based equality/hash and are not Entity identities.

The trusted host obtains `StudentSnapshot(student, saved_version)` through `get_student(student_id, sessions)` and receives the same snapshot shape after a committed create/replace. Replacement adds mandatory raw-integer `expected_version` (`snapshot.saved_version.value`); the input factory produces the typed value supplied to Repository Ports. Omission is invalid input, with no compatibility fallback. No GraphQL field is added.

Processing order is student ID → programme ID → name → email → valid mode → required replacement version → target existence → Domain outdated-version policy → Domain email-availability policy. The mode position preserves existing behavior; field order and stale-before-email are consistent with FR-013/FR-018. Snapshot reads pair details and version from one row/read.

Repository invokes a controlled Domain `Student.replace_details` transition on the existing confirmed identity before writing. It uses a guarded update matching both `student_id` and `saved_version`, advancing the version in the same statement. Under the immediate writer transaction, a post-check zero-row update is a defensive Core `VersionConflict` observation translated by Application to Domain `OutdatedVersion` (not a guessed success); target disappearance must be distinguished if the port is implemented with weaker isolation. Return no snapshot until commit. Do not reload/reapply stale replacements. Rejected/rolled-back changes do not advance the version. Old values restored later still receive a later version.

### Schema compatibility and provisioning

Fresh schemas include saved versions with the existing business-table primary-key/unique constraints. Initialization must inspect compatibility before any DDL/data change: old Student schemas, wrong version constraints or invalid stored versions are refused as storage/integrity failures without alteration. Compatible initialization is idempotent. No automatic migration, backfill, fabricated Student details, or silent version default for old rows is authorized.

Fresh Student creation uses version 1 explicitly. Subsequent Student changes must use the conditional trusted host path; direct unconditional updates are unsupported. Add a schema guard requiring every accepted Student update to advance `saved_version` by exactly 1, with strict integer/bounds checks. This prevents direct legacy updates from leaving stale comparison tokens valid; arbitrary SQL access is not an authorization boundary and cannot prove a caller supplied an expected version. Hosts must update their provisioning/update paths accordingly.

## Architecture and enrollment flow

1. Verify identity before persistence; known provider outage remains `IDENTITY_UNAVAILABLE`, negative verification remains generic `DENIED`.
2. Validate target StudentId, then apply Domain ownership. Invalid target input and mismatch retain their approved distinctions.
3. Validate CourseId immediately after ownership and before all prerequisite reads (FR-014).
4. Open the UoW and restore Student, Programme, and Course in that order. Return the first absent-record outcome; skip dependent checks.
5. Apply Domain duplicate policy, then Domain offering policy, stopping at the first rejection.
6. Invoke Repository `create_enrollment`; it INSERTs the pair, obtains its confirmed identity and invokes Domain creation without committing.
7. Application commits, then returns the confirmed Enrollment. All failure paths preserve FR-006, with one bounded pair-conflict replay as above.

## Verification and TDD evidence

### Evidence capture

Enrollment acceptance stays HTTP POST `/graphql` through Flask with real GraphQL and file-backed SQLite. Student acceptance uses the trusted `get_student`/`save_student` boundary with real SQLite. No new acceptance framework or dependency is introduced.

Begin each changed behavioral increment with an actual relevant acceptance failure, follow inner-layer TDD where useful, and retain Green after implementation/refactor consideration. Related cases may share an increment. Use the existing recorder's `implementation_state`, `implementation_state_after`, `activity`, `test_id`, timestamps, command, result, and output; these fields are already implemented and must not be planned as absent.

The existing validator permits historical records without state fields. Preserve those bytes and classify them as historical. New required v3.0.0 increments must be explicitly identified by the completion manifest/review and require full state/test/activity associations; the historical compatibility path cannot satisfy a new increment. Enforce test relevance, unchanged state during a run, ordered Red before Green without overlapping execution, successful Green, acceptance-first versus inner activity, and final-state freshness. Passing checks alone do not prove Outside-In TDD.

Expand exact-set acceptance inventory to `enrollment-1` through `enrollment-19` and `student-details-1` through `student-details-17`, retaining every existing parameterized identity (including all original Unicode variants). Collection counts alone cannot replace IDs. Pair all new lifecycle/version outcomes with real Repository contract tests and semantic review.

### Architecture fitness

Keep inward-dependency, framework-isolation, outbound independence, public type/conversion, and alias-aware construction checks. Production complete-Entity factory/reconstitution calls are permitted only in persistence Repository implementations; pure Value Object boundary factories remain permitted. Isolated Domain factory tests and explicit violating fixtures are recognized exceptions, not production entry points.

Behavioral Repository tests must prove acknowledged business-table INSERT precedes factory use and Domain rules execute before commit; duplicate identities fail database constraints; restored identity comes from stored state; explicit factory rejection and exceptions after INSERT roll back real SQLite with no committed Entity; Repository methods never commit part of a surrounding use case; pending Entities remain local and failed transactions return no successful creation result; uncertain commit requires reconciliation without destructive compensation. Do not test removed reservation or Entity-handle mechanisms. Use an injected factory seam to exercise explicit rejection where current valid component types have no real additional rejection; do not invent a business rule to manufacture the branch.

### Coverage scope

Retain coverage.py `branch=true`, `fail_under=100`, with all Domain/Application modules (including newly introduced/unimported modules). Cover every measured branch of each entire affected function/method, including unchanged branches. The existing project gate requires both statement and branch completeness. Branchless functions still require behavioral tests.

Only pure Protocol-signature modules may use coverage's default ellipsis omission, and the evidence validator must continue checking that shape. No business exclusion, changed-lines gate, `pragma: no cover`, or weakening tests to pass. Run strict mypy, Ruff lint/format, Import Linter, architecture and contract tests, installed-package tests, and real socket regressions.

## Remaining migration

| Current inspection | Required implementation work |
|---|---|
| Typed factories, reconstitution, integrity mapping already exist | Retain them; restrict production Entity call sites and enforce operation-local pending results |
| Application constructs Student and Enrollment before writes | Replace those calls and Entity-taking writes with Repository creation/replacement Ports |
| No persisted saved version, host read operation, or CAS | Add SavedVersion, StudentSnapshot, version outcomes, trusted retrieval, conditional update, compatibility checks and update guard |
| Entity construction precedes persistence | INSERT before Domain creation; keep pending results inside the operation, roll back rejection/failure and return success only after enclosing commit |
| Recorder already captures state/test/activity | Harden new-increment validation and review associations without rewriting history |
| Inventory covers enrollment 1–15 and Student 1–10 | Extend exact sets and acceptance cases for all current scenarios; preserve existing variants |

## Delivery and completion

Reassess [tasks.md](tasks.md) with `$speckit-tasks` after this design. Preserve completed historical tasks/evidence and append or amend remaining work based on current source. This planning run does not execute implementation or change task checkboxes.

Recommended cohesive increments: Repository identity confirmation and real rollback contracts; enrollment creation/commit integration; Student version/snapshot schema and read integration; conditional replacement/conflict/race behavior; exact inventory and evidence validation. Acceptance tests guide all of them; sequence shared dependencies before dependent behavior and verify every affected layer.

After implementation, run on the stable tree:

```bash
bash scripts/check-quality.sh
# Review raw checks and update evidence/reconciliation/review.json honestly.
.venv/bin/python -m scripts.assemble_evidence
.venv/bin/python -m scripts.check_evidence
```

Every mandatory check must run and pass with current evidence. Source/test/config changes require fresh final checks. Documentation-only planning checks are not implementation acceptance or historical TDD certification. See [quickstart.md](quickstart.md) for runnable validation and expected new outcomes.

## Constitution Check — Post-Design

**Post-design result: PASS for the documented design.** Research resolves each flagged planning uncertainty; the ADR and contracts define confirmation points, Repository entry points, factory/restoration inputs, transaction ownership, operation confinement and commit boundaries, rollback on explicit and exceptional failures, conditional revisions, acceptance boundaries, coverage, and evidence requirements. No constitutional waiver or unresolved design placeholder remains. Current source still requires the migration above; no execution/completion claim is made.

| Artifact | Purpose |
|---|---|
| [research.md](research.md) | Decisions, alternatives, sources, and flagged uncertainty amendments |
| [ADR-0001](adr/0001-entity-lifecycle-and-student-revisions.md) | Repository construction, atomic creation and conditional replacement trade-offs |
| [data-model.md](data-model.md) | Entity identity, saved versions, storage and transitions |
| [contracts/](contracts/) | Repository, Domain, trusted host, and GraphQL boundaries |
| [quickstart.md](quickstart.md) | Existing runnable checks plus required implementation validation |

## Complexity Tracking

No constitutional violation is justified or waived. Existing business-table constraints and enclosing transactions establish identity confirmation and atomic creation. Pending results stay local until commit, with no reservation table, Entity lifecycle handles or additional lifecycle abstractions. The existing StudentSnapshot wrapper carries required concurrency metadata; no service, surrogate business key or public management endpoint is introduced.
