# Tasks: Student Self-Enrollment — Remaining Alignment

**Updated:** 2026-10-22 | **Branch:** `001-enroll-course` | **Active:** T101–T128 (pending)

**Sources:** [spec](spec.md), [plan](plan.md), [shared D1–D5](../../.specify/memory/architecture-decisions.md), [research](research.md), [data model](data-model.md), [construction contract](contracts/domain-construction.md), [enrollment contract](contracts/enrollment-api.md), [Student contract](contracts/student-details.md), [quickstart](quickstart.md).

**Governance:** Constitution v2.0.0 is the last historically ratified version; proposed v2.1.0 requirements are requested feature-delivery constraints, not ratification. This file tracks remaining alignment, not a new feature implementation.

## Completed baseline (archival)

T001–T100 were marked complete in the prior task record. Preserve their original descriptions, decisions, evidence, reviews and status in Git history and `specs/001-enroll-course/evidence/`; do **not** execute them again. In particular, C1/T050 was reassessed under v2.0.0; T095–T100 verified the Unicode amendment. The last recorded result was **210 tests**, **15 enrollment scenarios**, **23 Student-detail cases**, **100% complete Core statement/branch coverage**, and passing final evidence for digest `c0dbcd8d151a61d8e71f2d7229c17b38b54fc56d7e19e808e305a51ce8aa9faa`. These are **historical claims**, not a pass for the forthcoming migration. See retained final validation and reconciliation review. The original T001–T100 wording remains available in the preceding Git revision of this file; do not erase or alter the underlying evidence.

## Active rules

- Inspect current code/tests/evidence before changes; preserve working behavior and completed work. No dependency upgrade, new endpoint, GraphQL reason, eligibility rule, schema migration, or reduced quality gate.
- **Application** orchestrates verification, repository misses, transactions and FR-009 order; **Domain** owns business predicates/invariants. Adapters translate external representations and may invoke supported Domain factories/reconstitution directly. Do not relocate orchestration into Domain solely for architecture aesthetics.
- Use acceptance-guided **Outside-In TDD** for genuinely missing behavior: meaningful behavioral Red → implementation → Green → consider Refactor. Passing legacy behavior is verification, not fabricated Red. Import/signature/environment failures alone are not behavioral Red. No per-assertion cycles, mandatory refactor changes or per-cycle commits.
- Apply shared **D1–D5**. Record new work with real implementation-state/order/test/activity associations; allow consolidated evidence. Never retrofit unsupported chronology to historical records. Preserve historical evidence bytes.
- Preserve all **15 enrollment** and **23 parameterized Student-detail** acceptance identities (including Unicode expansion and composition), complete Domain/Application **100% statement and branch coverage**, the constitutional whole-affected-business-function branch floor, and existing static, contract, architecture, installed-wheel and socket checks.
- `[P]` means test/document work on disjoint files may overlap after dependencies; never edit shared production files or measure evidence against a changing tree. Task completion requires verified results, not just an unchecked-to-checked change.

## Phase 11 — Baseline and evidence bootstrap

- [ ] **T101** Inspect current source against `plan.md` migration gaps; capture actual baseline/digest/revision in `evidence/reconciliation/alignment-baseline.json`. Archive current final checks, manifest, validation and review byte-for-byte in `evidence/history/pre-v2.1-alignment/` with verified SHA-256 index. Preserve earlier history.
- [ ] **T102** After T101, document and execute a temporary D4 bootstrap procedure in `evidence/README.md`: capture real before/after state digests, run times, command/test identities, acceptance/inner role and reviewable changes in `evidence/reconciliation/alignment-bootstrap.json`. Run existing HTTP and host acceptance suites as **verification** baselines; do not call them Red.

## Phase 12 — Shared foundations

**Evidence tooling** (T103–T106 sequential; use genuine bootstrap records until recorder support exists):

- [ ] **T103** Add behavioral capture tests in `tests/architecture/test_quality_gates.py`: before/after implementation states, order, selectors, acceptance-vs-inner context, consolidated/shared suites; meaningful Red, not missing CLI/import scaffolding.
- [ ] **T104** Extend `scripts/record.py` under D4 while retaining lightweight positional commands and lowercase stages; capture actual states and reviewable changes, run Green, preserve optional refactor/verification. No snapshots, hash chains, per-cycle commits or mandatory refactor artifact.
- [ ] **T105** Add validator tests: reject absent/defaulted state/time, unrelated tests, missing activity roles, reversed/overlapping order, changed-during-run state, failed Green and stale checks; accept valid consolidated and supported historical evidence.
- [ ] **T106** Update `scripts/assemble_evidence.py` and `scripts/check_evidence.py` to hash/reference D4 associations and enforce supported chronology without a fixed increment inventory. Preserve historical compatibility **without** treating old output-only evidence as new proof; retain all eight final checks, freshness, artifact hashes and acceptance inventory. Verify positive/negative fixtures.

**Construction and integrity** (after T106):

- [ ] **T107** Add Domain `InvalidPersistedState` in `domain/outcomes.py` and Core `DataIntegrityFailure(StorageFailure)` in `application/contracts.py` per D3. Declaration-only scaffolding; no new public reason or fabricated Red.
- [ ] **T108** Test then implement separate `.reconstitute(raw)` for ID, `StudentName`, `StudentEmail` values in `domain/values.py`. Invalid persisted state returns `InvalidPersistedState`; normal `.create(raw)` keeps existing validation results. Preserve exact opaque IDs, required nonblank text, original spelling and full-address Unicode `casefold()` (no normalization/trimming).
- [ ] **T109** Test then implement `Student.reconstitute` in `domain/models.py` from typed ID/programme/name/email. Preserve StudentId identity, dangling programme references, and restoration independent of current email availability. Invalid stored invariants yield `InvalidPersistedState`; do not yet change normal `Student.create` callers.
- [ ] **T110** Test supported-model factory/caller checker in `tests/architecture/test_boundaries.py`: all values, `VerifiedIdentity`, five entities, aliases/inherited factories/new modules, permitted internal construction and direct Adapter restoration, with allowed/violating fixtures. No duplicate import-graph engine or absolute Python privacy. Report production violations as pending until T120.

## Phase 13 — US1 enrollment migration

**Prerequisite:** T110. Preserve 15 HTTP scenarios, FR-009 ordering, durability, first-match rejection, concurrency and technical integrity classification.

- [ ] **T111** `[P]` Add acceptance/Application/SQLite tests for supported factory delegation, record restoration, corrupted saved state vs absence and unchanged public outcomes (`test_enrollment.py`, `test_identity.py`, `test_sqlite.py`). Record genuine missing-behavior Red; retain passing scenarios as verification.
- [ ] **T112** Test/implement typed factories and separate reconstitution for `Programme`, `Course`, `ProgrammeCourseOffering`, `Enrollment` in `domain/models.py`, plus `VerifiedIdentity.create(SubjectId)` in `domain/values.py`. Preserve pair association, existing many-to-many offering, no synthetic identity, no invented invariants/eligibility, and T109 Student restoration.
- [ ] **T113** Migrate `application/enroll.py`, identity adapter and ordinary US1 fixtures to supported `Enrollment`/`VerifiedIdentity` factories. Preserve **verification → StudentId → ownership → CourseId → Student → Programme → Course → duplicate → offering**, negative-verification privacy, Domain predicates, typed outcomes and one bounded pair-conflict replay. Test delegation/short-circuit behavior.
- [ ] **T114** Migrate SQLite row loaders to value-then-record `.reconstitute`, including Student reads shared with US2. Map `InvalidPersistedState` to Core `DataIntegrityFailure(StorageFailure)` and sanitized `PERSISTENCE_FAILURE`; keep `None` for actual absence, propagate unexpected programming faults, and do not recheck current offering/email admission. Verify corrupt/valid historical records.
- [ ] **T115** Run US1 checkpoint: all 15 acceptance cases, identity/conflict/retry/race/concurrency/fault, Waitress socket and installed-wheel tests. Confirm BEGIN IMMEDIATE, atomic pair uniqueness, commit-before-success, rollback, no compensation after commit, SDL and denial privacy. Retain state-associated **verification** results; not global completion.

## Phase 14 — US2 Student details migration

**Prerequisites:** T110 for T116; **T114 + T116** for T117. Shared Domain/SQLite production edits are serialized.

- [ ] **T116** `[P]` Add host acceptance/Application tests for typed Student creation, ordered ID/name/email validation, invalid input vs corrupt persisted data, and rejection preserving old details. Keep all 23 named cases/seven families; genuine Red only for missing behavior.
- [ ] **T117** Change `Student.create` to typed `StudentId`, `ProgrammeId`, `StudentName`, `StudentEmail`; convert raw fields in `application/student_details.py` through VO factories first. Preserve first-invalid-field order, create/replace semantics, own-email exemption, StudentId equality/hash and full-address `casefold()` email equality/hash. No programme-existence or email-syntax rules.
- [ ] **T118** Migrate ordinary Student constructors/fixtures and StudentSession/email-owner row decoding to supported APIs. Preserve deliberate corrupt/legacy and misuse fixtures, configured deterministic SQL functions, precise email-index conflicts, original spelling and legacy-schema refusal. Invalid saved state is technical integrity failure, not invalid input/conflict/not-found.
- [ ] **T119** Run US2 checkpoint: 23 Student cases including Unicode expansion/composition, cross-programme uniqueness, whitespace, own-email replacement, concurrency one-winner, unchanged state on rejection and commit-before-return. Confirm enrollment never writes Student and US1 regressions pass. Retain state-associated verification; not global completion.

## Phase 15 — Integration and completion

**Prerequisites:** T115 + T119.

- [ ] **T120** Enforce full factory/caller inventory and migrate remaining ordinary production/test constructor uses. Preserve internal constructors and explicit negative fixtures; verify aliases, all supported models, typed Entity inputs, direct Adapter restoration, structural/import checks and behavioral tests. No blanket exclusions.
- [ ] **T121** Verify semantic boundaries beyond imports: Domain business decisions; Application sequencing/transactions; Adapter conversion; input/business/integrity distinction; precise retry/cleanup and confirmed commits. Test and correct only actual gaps. Keep constitutional whole-function branch floor and stronger complete-Core coverage gate.
- [ ] **T122** `[P]` Update `README.md`, `quickstart.md` and `evidence/README.md` with **implemented** factory/restoration and recorder commands, internal integrity vs sanitized public errors; reference shared D1–D5. No speculative flags or ratification claims.
- [ ] **T123** `[P]` Review historical and new records in `evidence/reconciliation/alignment-history-review.json`. Preserve C1/T050/T100 and hashes; associate old states only when supported; distinguish acceptance-first/inner activity and genuinely evidenced Red/Green; report unresolvable gaps without inventing chronology.
- [ ] **T124** After T122/T123, run `bash scripts/check-quality.sh` on stable source/tests/config. Require all eight checks, 15+23 scenario identities, architecture/contracts, real socket/wheel, strict mypy, Ruff, Import Linter and 100% full-Core statement/branch coverage. Preserve raw failures and recapture after changes.
- [ ] **T125** Review current results/evidence in `evidence/reconciliation/review.json` against T124 digest; distinguish structural, behavioral and semantic proof. Pass only with supported new-work chronology and all mandatory gates; disclose gaps honestly.
- [ ] **T126** Run `.venv/bin/python -m scripts.assemble_evidence`; ensure manifest hashes/references checks, review, current state-associated runs, bootstrap and historical support with matching digest. Assembly ≠ validation.
- [ ] **T127** Run `.venv/bin/python -m scripts.check_evidence`; require `passed: true`, no mandatory gaps, fresh matching digest and complete artifacts/scenarios. If failing, fix owning work and rerun T124–T127 as needed; do not weaken chronology validation.
- [ ] **T128** Only after T127 passes, update task checkboxes and concise actual outcomes (counts/digest/evidence links). Preserve T001–T100 in Git/evidence, report unresolved blockers, and **do not** claim Constitution v2.1.0 ratification.

## Active dependencies

```text
T101 → T102 → T103 → T104 → T105 → T106 → T107 → T108 → T109 → T110
T110 → T111 → T112 → T113 → T114 → T115                [US1]
T110 → T116 ────────────────────────┐                    [US2 tests]
T114 + T116 → T117 → T118 → T119    ┘                    [US2 integration]
T115 + T119 → T120 → T121 → (T122 || T123) → T124 → T125 → T126 → T127 → T128
```

`[P]` T111/T116 may prepare disjoint tests after T110; T122/T123 may proceed independently after T121. Do not run state-measured tests during concurrent source changes. Do not parallelize `domain/models.py`, `persistence/sqlite.py` or final evidence capture.

**Traceability:** D4/evidence T102–T106,T123–T127; construction/restoration D2/D3 T107–T120; FR-001–FR-010/SC-001–SC-004 T111–T115,T120–T127; FR-011–FR-013/SC-005–SC-007 T109,T116–T119,T124–T127; architecture/quality D1/D5 T110,T120–T127; historical preservation T101–T102,T123,T125–T128.

**Status:** 100 historically completed; 28 active pending. No implementation or verification is claimed by this task edit.
