# Implementation Plan: Student Self-Enrollment

**Branch:** `001-enroll-course` | **Date:** 2026-10-22 | **Spec:** [spec.md](spec.md)

**Baseline:** Specification at `e74543e`. Constitution v2.0.0 is the last historically recorded ratified version. Proposed v2.1.0 requirements apply as explicitly requested *feature delivery constraints*, not ratified project policy. This plan neither ratifies them nor certifies implementation compliance.

## Summary

Complete the remaining migration of Domain factories, controlled reconstitution, persisted-state integrity classification, and TDD/architecture evidence. Preserve implemented enrollment and Student-detail behavior, public contracts, dependencies and quality gates. Apply shared [architecture decisions D1–D5](../../.specify/memory/architecture-decisions.md) rather than restating their mechanisms.

Existing enrollment, Student details, expected failure results, bounded conflict replay and basic evidence capture are implemented. Reconcile tasks against actual source before making changes; do not redo completed behavior or fabricate historical TDD evidence.

## Technical Context

| Area | Decision |
|---|---|
| Runtime | Python 3.12 (`>=3.12,<3.13`), Linux, single threaded WSGI process |
| HTTP / GraphQL | Flask `>=3.1,<3.2` handles HTTP; graphql-core `>=3.3,<3.4` executes SDL-first GraphQL; Waitress serves WSGI |
| Persistence | File-backed SQLite (`sqlite3`), five persisted record types, worker-owned connections; no ORM |
| Public boundaries | Existing POST `/graphql` enrollment mutation; internal trusted Python Student create/replace operation |
| Tests | pytest, Flask test client, real temporary SQLite, injected identity verifier, port spies, real Waitress socket and installed-wheel checks |
| Quality | Strict mypy, Ruff lint/format, Import Linter, coverage.py, architecture/contract tests, final evidence validation |
| Constraints | Retain `pyproject.toml` and `uv.lock` without dependency upgrades; no new API, service, business eligibility, deployment topology or performance promise |

Retain the five-second bounded SQLite lock wait, classified as a technical failure.

## Constitution Check

**Design-level PASS only:** no waiver requested. Actual migration, execution evidence and final-state quality checks remain outstanding.

| Principle | Design disposition / remaining implementation obligation |
|---|---|
| I. Inward dependencies | Keep Application-owned Ports and adapter isolation; D1/D5 govern supported adapter construction/reconstitution |
| II. Domain integrity / Full Bridge | D2/D3 and [construction contract](contracts/domain-construction.md) specify missing factories, typed Entity inputs and restoration/error mapping |
| III. Outside-In TDD | D4 specifies state-associated Red/Green and acceptance/inner activity evidence; recorder/validator migration pending |
| IV. Fitness / coverage | Add factory/caller verification; separate structural checks from semantic behavioral verification; retain coverage gates |
| V. Evidence / quality | Preserve existing final checks, then rerun and review against final implementation state |

## Design References and Structure

| Source of truth | Scope |
|---|---|
| [spec.md](spec.md) | FR-001–FR-013, FR-009 order, scenarios and success criteria |
| [Shared decisions D1–D5](../../.specify/memory/architecture-decisions.md) | Ports, factories, error mapping, evidence and fitness conventions |
| [research.md](research.md) | Alternatives and inspected migration gaps |
| [data-model.md](data-model.md) | Model relationships, text/equality semantics and lifecycle |
| [Domain construction contract](contracts/domain-construction.md) | Typed factories and controlled reconstitution per model |
| [Enrollment contract](contracts/enrollment-api.md) and [SDL](contracts/schema.graphqls) | Existing GraphQL/API behavior and result mapping |
| [Student details contract](contracts/student-details.md) | Internal host operation and uniqueness behavior |
| [quickstart.md](quickstart.md) | Validation and final-check instructions |

```text
src/enrollment/
  domain/{values,models,policies,outcomes}.py
  application/{enroll,student_details,contracts,ports,student_ports}.py
  adapters/{graphql,http,persistence,identity}/
  bootstrap.py
tests/{acceptance,domain,application,adapters,architecture}/
scripts/{record,assemble_evidence,check_evidence,check_quality}.py
specs/001-enroll-course/evidence/{reconciliation,final,history}/
```

Extend existing modules. HTTP-to-GraphQL adapter composition is permitted; other sibling adapters remain independent. Bootstrap owns dependency injection and schema wiring; Core remains framework-free.

## Architecture and Enrollment Flow

**Ownership:** Domain owns business authorization predicates, duplicate/offering policies, invariants and state transitions. Application owns identity-verification coordination, Repository absence handling, transaction orchestration and **exact FR-009 sequencing**. It may short-circuit on typed Domain outcomes but must not reproduce Domain business predicates. No Domain Service is required merely to move Application orchestration into Domain.

IdentityVerifier and enrollment/Student UoW Protocols belong to Application. Domain imports neither Application contracts nor verifier ports. Adapters may translate external values through supported Domain factories and reconstitution without owning business decisions. Do not introduce redundant DTOs or duplicate validation.

**Ordered enrollment checks:**

1. Verify credential; negative verification yields generic `DENIED` before Domain ownership or persistence. Provider outage is a separate technical failure.
2. Validate target `StudentId`; apply Domain ownership policy to `VerifiedIdentity` and target; reject non-owner before persistence.
3. Validate `CourseId`.
4. Within the transaction, load Student, Programme and Course in order; Application returns their distinct missing-record outcomes.
5. Invoke Domain duplicate policy, then Domain offering-eligibility policy; stop at first rejection.
6. Create Enrollment through its supported Domain factory; add, commit, then report success.

Missing prerequisite records are not interpreted as eligibility failures. Verified identity does not establish Student existence. Preserve the exact rejection precedence, GraphQL reasons and identity timing in the contracts.

**Transaction:** Use a request/worker-owned SQLite connection, `autocommit=True`, explicit `BEGIN IMMEDIATE` before prerequisite reads, then SQL `COMMIT`/`ROLLBACK` and close. No network call occurs within the transaction. Preserve save-time eligibility, pair uniqueness, no mutation on rejection, and no compensating deletion after confirmed commit/response loss. Flask teardown must not own transaction completion.

Port results remain `Added | PairConflict` for enrollment and `Saved | EmailKeyConflict` for Student writes. A precise `PairConflict` triggers rollback/close and at most one fresh, full ordered attempt; a second conflict becomes technical `StorageFailure`, never a guessed duplicate. Only the named email unique-index conflict maps to `EmailKeyConflict`; driver exceptions remain inside adapters.

**Transport:** Keep POST-only Flask routing, disabled automatic OPTIONS/static route, sanitized errors with correct HTTP status/Allow headers, stable SDL/union mappings and one reusable GraphQL schema. Framework/WSGI/SQLite/provider types never enter Core public contracts.

## Student Details and Data Integrity

Retain required nonblank Student name/email, original spelling, full-string Unicode `str.casefold()` equality (including expansions), significant whitespace and composition non-equivalence. Do not trim, validate email syntax, apply provider aliases, or add a Programme-existence prerequisite. `StudentEmail` equality/hash derive from its comparison key; Student identity/equality/hash derive from `StudentId` alone.

The existing internal host create/replace operation validates IDs, name and email in that order; Application obtains the email-key owner, invokes Domain email-availability policy and saves atomically. Preserve distinct invalid-field, existing-create, missing-replace and email-conflict outcomes. Enrollment UoW does not gain Student write methods.

Keep Domain-backed deterministic SQL functions registered on every relevant connection, required-text constraints and unique `students_email_key` expression index. Missing registration fails closed; no forged separate stored key, `REPLACE`/`IGNORE`, automatic legacy backfill or silent legacy-schema migration. Compatible initialization is idempotent; incompatible legacy schemas fail without mutation. Detailed rules remain in [data-model.md](data-model.md) and [Student contract](contracts/student-details.md).

## Remaining Migration

| Location | Required change |
|---|---|
| `domain/values.py` | Retain existing identifier/text factories; add `VerifiedIdentity.create(SubjectId)` after trusted verification |
| `domain/models.py` | Make Student/Enrollment factories accept validated Domain components; add Programme/Course/ProgrammeCourseOffering factories |
| Persisted Domain models | Add separate controlled `.reconstitute` APIs and Domain `InvalidPersistedState` outcomes (D2/D3) |
| `application/student_details.py` | Convert raw fields through Value Object factories before typed Student creation; retain first-invalid-field ordering |
| `application/enroll.py`, identity adapter | Replace normal direct Entity/VerifiedIdentity constructors with supported factories at existing decision points |
| Persistence row loaders | Reconstitute values then records; map invalid stored state to Application `DataIntegrityFailure(StorageFailure)` |
| Tests, callers, fixtures | Update ordinary constructor callers; add non-vacuous model inventory and alias-aware factory/caller checks, plus behavioral restoration tests |
| Recorder, assembler, validator | Add implementation-state and acceptance/inner associations per D4; preserve historical evidence bytes |

Value Object factories accept raw representations; Entity factories accept validated Domain Types. Factories are required even when no extra cross-field constraint exists. Guarded internal constructors remain implementation details; do not require absolute Python privacy. Keep intentional internal-misuse negative tests.

Reconstitution enforces persisted-state invariants but does **not** rerun current offering eligibility or contextual email availability. Domain `InvalidPersistedState` maps through Core `DataIntegrityFailure(StorageFailure)` to the existing sanitized technical result, never absence, invalid request, business conflict or an added FR-009 step. Unexpected programming/contract failures must not be converted into business rejections. Cleanup preserves the primary failure and confirmed commits.

## Verification and TDD Evidence

Apply shared D4/D5 without duplicating tooling specifications here.

- Use acceptance-guided **cohesive behavioral increments**: relevant expected behavioral Red before new behavior, then Green; consider Refactor and retain Green. Shared tests may cover multiple layers. Pure refactors begin Green. Import/configuration/signature failures alone are not behavioral Red.
- Associate Red/Green runs with identifiable implementation states, execution order, increment/test identity and reviewable changes; distinguish acceptance-first from inner activity. Consolidated records are allowed. No per-cycle commit, exhaustive snapshots, fixed increment inventory or mandatory refactor artifact.
- Reject unrelated Red/Green, missing or defaulted chronology, failing Green, changed-during-run state and stale final evidence. Preserve historical records without inventing unsupported chronology.
- Use Import Linter for inward dependencies and adapter isolation; focused checks for public framework types, dynamic escapes, supported factory usage and reconstitution. Behavioral tests and explicit review verify semantic conversion, error classification and Domain policy ownership; static imports alone cannot prove these.
- Retain **100% statement and branch coverage for the complete Domain/Application Core**, including unimported modules and business behavior elsewhere. The constitutional minimum also covers every entire changed/new business-logic function, including unchanged branches. Preserve strict static, architecture, contract, acceptance and regression gates; no exclusions hiding business logic.

Preserve all **15 enrollment acceptance scenarios** and **23 parameterized Student acceptance identities** spanning seven Student scenario families, including Unicode expansion/composition. Keep real SQLite concurrency/rollback, Waitress socket and installed-package checks. A historical Green or coverage percentage alone does not certify TDD or current completion.

## Delivery and Completion

1. Reconcile `tasks.md` with current source and previously completed work; retain C1/T050 and T095–T100 historical records.
2. Extend/verify evidence capture and validator before making new TDD chronology claims; test both valid consolidated records and invalid/missing associations.
3. Implement remaining factory, reconstitution, caller and integrity migrations using appropriate acceptance-guided increments; extend structural and behavioral architecture checks.
4. Run all mandatory final-state tests, contracts, coverage, static checks and evidence review. Re-run after any source/test/config change.

```bash
bash scripts/check-quality.sh
# Review raw execution and quality results; update evidence/reconciliation/review.json.
.venv/bin/python -m scripts.assemble_evidence
.venv/bin/python -m scripts.check_evidence
```

Any missing, failed, skipped, blocked or stale mandatory gate prevents a completion claim. This plan changes no source, tasks, evidence or constitutional approval. **Next workflow:** `$speckit-tasks`.

## Complexity Tracking

No constitutional waiver, additional infrastructure or new service is introduced. Detailed cross-feature conventions remain in D1–D5 and linked contracts.
