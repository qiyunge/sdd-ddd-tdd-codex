# Execution evidence

Use the lightweight recorder from the repository root:

```bash
.venv/bin/python -m scripts.record student-details red .venv/bin/pytest tests/acceptance/test_student_details.py -q
.venv/bin/python -m scripts.record student-details green .venv/bin/pytest tests/acceptance/test_student_details.py -q
```

Execute Red before implementing genuinely missing behavior and Green after the
cohesive increment. Each record retains the actual command, output, exit result and
execution times under `evidence/reconciliation/`. Related behaviors may share an
increment and records may cover several layers. Optional `refactor` or `verification`
runs retain additional results; no separate no-refactor artifact is required.
Do not manufacture failures when behavior already works. Import/constructor/schema
setup/environment failures do not count as behavioral Red. Consider refactoring and
keep relevant tests passing. Passing tests and coverage alone do not establish TDD.

Final sequence:

1. `bash scripts/check-quality.sh` captures all final check results.
2. Review actual new/historical evidence and final results; record the current
   decision separately in `evidence/reconciliation/review.json`.
3. `.venv/bin/python -m scripts.assemble_evidence` hashes/references execution records,
   final checks and current review without approving them.
4. `.venv/bin/python -m scripts.check_evidence` validates freshness, coverage,
   acceptance identities, execution references and review. Any missing/failed check
   prevents completion. Source/test/config changes require final recapture/review.

Constitution IV requires 100% branches for each whole affected business function.
The approved project gate remains stricter: complete Core 100% statement and branch
coverage, including unimported modules; no business exclusions. Default ellipsis
exclusions are permitted only in structurally declarative Protocol modules.

Historical records and original review remain unchanged. `history-index.json` and
`evidence/history/pre-reconciliation/` preserve original final artifact hashes/bytes.
The archived review reassessed grouped work under constitution v2.0.0 using actual
retained commands/results. The active review is now governed by v3.0.0; neither
review rewrites history or infers TDD from final Green.

## Constitution v2.3.1 capture

`specs/001-enroll-course/evidence/reconciliation/alignment-baseline.json` records the
pre-migration digest of `src/`, `tests/`, `scripts/`, `pyproject.toml`, and `uv.lock`.
`evidence/history/pre-v231-alignment/` is a byte copy of the previous final artifacts,
with SHA-256 names in `index.json`.

New recorder output adds these fields to each run:

- `implementation_state`: digest before the command
- `implementation_state_after`: digest after the command; a difference is a changed-during-run failure
- `test_id`: the pytest target, which must appear in the command
- `activity`: `acceptance` when the command targets `tests/acceptance`, otherwise `inner`
- `started_ns` and `finished_ns`: execution order

The positional command form is unchanged. Passing HTTP and host suites recorded before
new behavior are `verification` baselines, not Red. Historical files that lack these
fields stay unchanged and are not v2.3.1 chronology.

```bash
.venv/bin/python -m scripts.record us1-checkpoint verification .venv/bin/pytest tests/acceptance/test_enrollment.py tests/acceptance/test_concurrency.py tests/acceptance/test_eligibility_races.py tests/acceptance/test_retry.py tests/adapters/test_server.py tests/adapters/test_package_resources.py -q
.venv/bin/python -m scripts.record us2-checkpoint verification .venv/bin/pytest tests/acceptance/test_student_details.py tests/acceptance/test_student_record_integrity.py -q
```

Supported construction is `Identifier.create` / `RequiredText.create` /
`SavedVersion.create` for raw or stored input with identical invariants,
`VerifiedIdentity.create(SubjectId)`, and
`Student.create`, `Programme.create`, `Course.create`, `ProgrammeCourseOffering.create`,
and `Enrollment.create` for validated Domain values. Record `.reconstitute` does not
replay offering eligibility or email availability.

## Constitution v3.0.0 increments

`reconciliation/v300-increments.json` declares the required lifecycle, snapshot/schema,
conditional replacement and gate increments and their acceptance/inner associations.
`v300-baseline.json` indexes verified original bytes under
`history/pre-v300-alignment/`; `v300-baseline-inventory.json` retains exact original
node/parameter identities. All pre-v300 records remain historical and cannot satisfy
new required cycles. Baseline passing runs are verification, never manufactured Red.

```bash
.venv/bin/python -m scripts.record v300-lifecycle red .venv/bin/pytest tests/acceptance/test_enrollment.py -q
.venv/bin/python -m scripts.record v300-lifecycle red .venv/bin/pytest tests/adapters/test_repository_lifecycle.py -q
.venv/bin/python -m scripts.record v300-lifecycle green .venv/bin/pytest tests/acceptance/test_enrollment.py -q
```

Use the same declared increment for associated acceptance-first and inner cycles.
Keep source/tests/config stable during runs and executions nonoverlapping.
Executable/module names alone do not identify tests; multi-test commands are
selections and retain all target/filter context. Consider refactoring and record
passing verification afterward; historical metadata is never silently defaulted.

The recorder locates pytest inside direct executable, `python -m pytest`, and
`python -m coverage run -m pytest` commands. Interpreter/module switches do not
become test identities. Pytest targets, node IDs, marker filters and `-k` expressions
remain part of the recorded selection.

`reconciliation/v300-review.json` records the current semantic and chronology
review; `reconciliation/review.json` is its active assembly input. Both bind the
final implementation digest and declared required increments. The manifest hashes
the declaration, baseline inventory, reviews, checks, required execution records
and preserved historical references. Exact validation covers 19 enrollment and 17
Student families, every mandatory parameter variant and every baseline acceptance
node; wrong labels, missing/duplicate/skipped cases and stale reviews fail.

An early v300-gates attempt recorded the pytest executable as its test identity.
Its original bytes remain available under `rejected_execution_records` with a
review reason and manifest hash. It cannot satisfy any required cycle. Independently
valid recorded gate Red/Green runs supply that proof. This classification is
explicit and checked: a valid execution cannot be hidden as rejected, and all
required cycles must pass after rejected attempts are removed. Historical records
without sufficient associations remain historical rather than fabricated proof.

The trusted host contract returns `StudentSnapshot` after read/create/replacement
commit and cleanup. Replacement supplies raw `snapshot.saved_version.value` and
returns OutdatedVersion for a stale snapshot, without an automatic retry. See the
[runnable host example](../../../README.md#required-student-details-and-host-integration).
Schema initialization refuses incompatible stored versions/guards without changing
the database. Uncertain commit returns a technical failure and requires a later
independent read; it never authorizes deletion or reversal of potentially committed
records. Enrollment SDL and rejection vocabulary remain unchanged.

T192's `v300-exact-identifiers` increment records acceptance failure before the
Repository failures for valid U+0000-prefixed identifiers. Domain factory cases
already passed and are verification, not a new Domain Red. Identifier constraints
now measure `length(CAST(identifier AS BLOB))` while retaining the TEXT check,
so nonempty NUL-containing identities survive all five tables unchanged. The
acceptance cases cover committed snapshots, conditional replacement and HTTP
enrollment; Repository tests cover provisioning/restoration and schema refusal.
The corrected Student column-constraint fixture supplies valid name, email and
version fields so those unrelated constraints cannot mask the identifier check.
The exact inventory includes the three new Student scenario-11 variants.
`history/pre-t192-alignment/index.json` hashes the preserved current evidence
bytes from before this increment. Databases using the prior TEXT-length checks
are incompatible and remain unchanged when initialization refuses them; migration
remains an external host responsibility.
