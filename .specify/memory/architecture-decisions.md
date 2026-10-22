# Shared Architecture and Verification Decisions

**Recorded**: 2026-10-22 | **Context**: requested planning alignment with the current
feature specification and proposed Constitution v2.1.0. These are shared implementation
conventions, not constitutional ratification or a claim that migration is implemented.
Feature Plans reference these decisions; changes affecting multiple features require
explicit review and an updated shared record. Independent feature overrides are prohibited.

## D1. Existing project boundaries and tools — retained

- Application owns use-case orchestration Ports (currently identity verification,
  enrollment UoW, and Student UoW). Domain owns decisions and invariants. A future
  Domain-owned Port requires a business-policy capability rather than orchestration;
  record that shared boundary decision before dependent implementation.
- The current Core is framework-free. Application's constitutional permission to use
  frameworks remains; introducing an Application framework or framework-owned public
  contract requires shared review, not an independent Feature Plan exception.
- Domain/Application/adapters/bootstrap boundaries and the declared HTTP-to-GraphQL
  adapter composition follow `pyproject.toml` Import Linter contracts. Bootstrap is
  the composition root. No cross-context communication or distributed transaction
  convention is introduced by this record.
- Retain Python 3.12 and locked dependencies; pytest, Import Linter, strict mypy,
  Ruff, and coverage.py remain shared gates. Complete Domain/Application 100% statement
  and branch coverage, including unimported modules, remains stronger than the
  whole-affected-business-function branch minimum. No business exclusions or
  changed-line gate; only verified declarative Protocol ellipses may be excluded.
- Relevant sources: `README.md`, `pyproject.toml`, `uv.lock`,
  `tests/architecture/test_boundaries.py`, `scripts/check_quality.py`, and
  `specs/001-enroll-course/evidence/README.md`. This record consolidates existing
  practices rather than selecting a new technology or lowering any quality gate.

## D2. Shared normal-creation and reconstitution APIs — migration decision

- Normal creation uses `Type.create(...)` for every Domain Value Object and Entity,
  including models with no additional cross-field constraints. Existing inherited
  identifier/text factories follow this convention. Value factories accept raw
  representations; Entity factories accept validated Domain component types.
  `VerifiedIdentity.create(SubjectId)` is called only after trusted verification.
- Return the valid model or its explicit applicable validation/business failure
  outcome. A factory with no expected failure for its validated inputs need not invent
  a rejection. Do not make every entity perform contextual policy checks: Application
  supplies facts to Domain policies in the declared use-case order.
- Persisted models and their stored component values use separate
  `Type.reconstitute(...)` APIs. Value reconstitution validates stored primitives;
  Entity reconstitution validates typed components and persisted entity invariants.
  Pure invariant predicates may be shared; creation-only eligibility is never replayed.
  `VerifiedIdentity` is not persisted by the current project and gets no artificial
  restoration operation.
- Internal constructors remain implementation details; absolute Python privacy,
  `init=False`, or a token mechanism is not prescribed. External production callers
  and ordinary test setup use supported APIs. Tests intentionally probing internal
  misuse and isolated violating fixtures remain explicitly identified negative cases.
- Maintain a model-role inventory covering identifiers, required text,
  VerifiedIdentity, Student, Programme, Course, ProgrammeCourseOffering and Enrollment.
  Outcome carriers are classified separately from business models. Fitness checks
  verify factory presence and supported callers with alias-aware checks, including
  newly introduced model types; do not infer semantic conformance from method names.

## D3. Data-integrity failure contract — migration decision

- Domain reconstitution returns a Domain-owned `InvalidPersistedState` outcome when
  persisted-state validation fails. This is a data-integrity outcome, not an ordinary
  input-validation or business rejection. Domain imports no Application error type.
- Persistence Adapters directly call supported reconstitution while implementing
  Core-owned Ports. They translate invalid persisted components/records into a
  Core-owned `DataIntegrityFailure`, a subtype of existing Application `StorageFailure`.
  This preserves existing operational-error catches while making classification
  identifiable internally. Do not catch arbitrary programming errors as corruption.
- Application retains the sanitized public `PERSISTENCE_FAILURE` / host
  `StudentStorageFailure` outcome. Record the integrity category in private diagnostics
  rather than add GraphQL reasons or expose invalid values. Absence remains `None`;
  precise write conflicts remain returned conflict values; availability and unrelated
  database errors remain their documented technical failures.
- Internal constructor misuse outside persisted-data validation remains a programming
  contract violation; it is not automatically a data-integrity or business failure.

## D4. Reviewable lightweight evidence — migration decision

- Retain repository-local evidence and immutable historical records. Current storage
  is `specs/<feature>/evidence/`, with execution records under `reconciliation/`, final
  capture under `final/`, and superseded results under `history/`. Retain evidence for
  as long as its implementation/completion claims are retained in repository history;
  removal requires explicit shared review, not silent recorder cleanup.
- Preserve actual command/test selectors, result/output reference, increment identity,
  start/end execution times and Red/Green stage. Add implementation-state identities
  before and after each run using the existing source/tests/scripts/config digest
  algorithm; retain a revision or reviewable working-tree/change reference so reviewers
  can associate those identities with the behavior implemented between runs. A commit
  per cycle, source snapshots, or a chain of every edit is not required. Changes during
  a measured run invalidate that run for chronology claims until assessed/rerun.
- Associate evidence with the behavioral increment and the relevant executed test
  identities. Identify acceptance-first activity and subsequent inner TDD activity
  separately in run/review context, including which responsibilities a shared suite
  exercises. Shared tests and consolidated records remain permitted; no separate test
  suite per layer or per assertion is required.
- Validation checks completeness, actual ordering, state association and passing Green.
  Review determines whether Red failed for the intended missing behavior and whether
  the acceptance-guided implementation chronology is supported. Output containing
  `AssertionError`, timestamps, differing hashes, or a final pass alone is insufficient.
- Historical evidence keeps its original bytes. A separate review may associate it
  with existing revision/change records; missing chronology remains an explicit gap.
  Never backfill invented state identifiers or manufacture Red for completed behavior.
- Retain the current final pipeline: quality capture, current review, manifest assembly,
  evidence validation. Source/test/config changes invalidate final digests and require
  recapture and review. Documentation alignment alone does not certify a new completion
  claim; prior verification remains a historical result under its original baseline.

## D5. Structural versus semantic fitness — retained and clarified

- Import Linter enforces declared static dependencies; focused checks cover public
  type annotations, dynamic dependency escapes and supported construction callers.
  Allowed/violating fixtures establish detection scope, including aliases/new modules.
- Behavioral Domain, converter/adapter, Application and acceptance contract tests verify
  invariant outcomes, representation conversion, error classification and business
  ownership/short circuits. Explicit review assesses semantic leakage and business
  decisions that static dependency graphs or annotations do not establish.
- Review evidence names the structural rule checks, behavioral contracts and reviewed
  semantic responsibilities separately. Passing dependency checks is never reported
  as proof of semantic boundary isolation. Preserve direct Adapter factory and
  reconstitution access, Application orchestration, and Domain business authority.

## Decision review and scope

D1 and the existing portions of D4/D5 preserve the cited repository policies. D2/D3
and the state/role association additions in D4 are recorded design changes required by
the user's updated feature constraints; implementation and negative-fixture verification
remain pending. The planning review records compatibility and migration in the feature
plan. This is not Project Owner ratification of Constitution v2.1.0. Other project-wide
questions outside these decisions remain open until dependent implementation needs them.
