# Quickstart Validation Guide: Constitution v3.0.0

This guide validates the target [plan](plan.md), [ADR-0001](adr/0001-entity-lifecycle-and-student-revisions.md), and contracts. Repository/version changes are not yet implemented. The existing test commands run now; passing the current suite does not establish the new acceptance outcomes until those cases and the revised inventory exist.

## Prerequisites and setup

Use Linux, Python 3.12, uv, a writable local temporary directory and file-backed SQLite on a local filesystem. Initial dependency synchronization needs download access. Keep uv.lock and the existing dependency versions. Socket tests need an available local ephemeral loopback port; wheel tests need a writable uv cache. These environment requirements are distinct from behavioral failures.

```bash
uv sync --frozen --dev --python 3.12
uv run python --version
uv run pytest tests/acceptance -q
```

Expected: Python 3.12 and current acceptance behavior. After implementation, the mandatory exact inventory must include enrollment-1 through enrollment-19 and student-details-1 through student-details-17, retaining every original parameterized case and Unicode variant. A total collected-test count is insufficient.

Fresh initialization uses the production connection setup and revised compatible schema. Hosts must provision valid prerequisite records and supply trusted identity verification before production serving. Deterministic verification exists only in tests. Reject incompatible/old schemas unchanged; this guide does not authorize migration/backfill or invent Student details/versions.

## Focused feedback commands

```bash
uv run pytest tests/domain -q
uv run pytest tests/application -q
uv run pytest tests/adapters -q
uv run pytest tests/architecture -q
uv run pytest tests/acceptance -q
uv run pytest tests/adapters/test_server.py -q
uv run pytest tests/adapters/test_package_resources.py -q
```

Tests may span layers through meaningful public boundaries. Pure Core tests require no Flask context. HTTP acceptance uses Flask's test client, real GraphQL, credential headers, a verifier double and SQLite; engine-only execution cannot replace that boundary. Waitress separately proves sockets/workers. Installed-wheel validation runs outside the editable checkout with packaged schemas.

## Enrollment acceptance

Use POST /graphql with the unchanged [SDL](contracts/schema.graphqls), neutral credential adaptation, independent request contexts and real worker-owned connections. Expected union outcomes use HTTP 200; inspect the union/reason, not status alone.

| US1 scenarios | Expected behavior |
|---|---|
| 1–2 | Eligible/shared-course enrollment commits exactly one retrievable pair. |
| 3 | Eligibility is assessed at the serialized save decision; a change committed before its reads is observed, a writer arriving after BEGIN IMMEDIATE waits and does not invalidate the prior commit. |
| 4–7 | Missing Student/Programme/Course or ineligible offering yields the approved first applicable reason; dependent checks are skipped. |
| 8–10 | Duplicates/lost-response retry preserve the saved pair; concurrent eligible attempts yield one success and one duplicate when visible. One unresolved full pair-conflict replay yields technical failure, not guessed duplication. |
| 11–12 | Failed saving leaves no partial pair; duplicate precedes offering rejection and avoids the offering lookup. |
| 13–15 | Negative verification/mismatch gives identical generic denial with no persistence; unrelated valid concurrent work may commit. |
| 16 | Explicit factory rejection/exception after INSERT rolls back actual SQLite changes, leaves no committed enrollment, and exposes no successful or reusable canceled creation result. |
| 17 | Definite failed commit produces no success/partial enrollment; pending creation results remain inside the operation and are discarded. |
| 18 | Valid saved enrollment restores with the same identity after creation-only eligibility changes. |
| 19 | After ownership, unusable CourseId yields INVALID_REQUEST before any prerequisite lookup, even if Student/Programme is missing. Identity/ownership denial still comes first. |

Keep all existing transport/schema tests: ID coercion, variables/operationName, nullability, union/enum mapping, safe errors, no extra routes/GET/OPTIONS surface, no lazy persistence during output, and no external types in Core. Do not weaken production foreign keys to construct impossible legacy scenarios; use controlled legacy fixtures or focused port contracts.

## Trusted Student acceptance

Use the host-only get_student/save_student operations described in the [Student contract](contracts/student-details.md), against real SQLite. Once implemented, obtain StudentSnapshot before replacement and pass snapshot.saved_version.value as the raw expected_version (Repository Ports receive the validated SavedVersion). A replacement test must never auto-refresh a deliberately old version. Existing callers that omit the required version must be updated.

| US2 scenarios | Expected behavior |
|---|---|
| 1–2 | Nonblank name/email accepted exactly; invalid normal input rejected and corrupt saved details reported as integrity completion failure. |
| 3–4 | Complete-address full Unicode case folding, including Straße/STRASSE expansion; significant spaces and composition forms remain distinct as specified. |
| 5–7 | Self-email retention/case change succeeds with a current version; different Students cannot claim the same caseless email; rejected change leaves current committed state intact. |
| 8–10 | Create-existing/replace-missing retain distinct outcomes; multiple defects follow approved field order. |
| 11–13 | Successful creation retains confirmed identity/state/version; definite pre-commit failure leaves zero committed rejected Entities; failed replacement preserves current committed details/version. |
| 14 | Two valid full replacements based on one saved version yield one committed new snapshot and one OutdatedVersion, without mixed fields or overwriting the winner. |
| 15 | Explicit reload and retry can succeed against the then-current version; another intervening save can make it outdated again. No silent replay. |
| 16 | Missing/unusable expected_version is invalid input, never unconditional replacement. |
| 17 | Old-version retry after committed response loss is outdated. Uncertain commit returns failure without destructive compensation. |

Also verify snapshot read consistency/no lazy connection, bool/noninteger/range rejection, same-detail version advancement, A→B→A without token reuse, maximum-version technical failure, stale-before-email, input-version-before-target lookup, missing-target-before-stale, corrupt persisted version, schema refusal and the SQL version-advancement guard. Version checks do not change StudentId-based equality/hash or add GraphQL fields.

## Real Repository and transaction validation

Use separate connections and bounded events/barriers, not sleeps. Never put a two-party barrier after a single-writer lock acquisition. Each thread creates, uses and closes its own connection; no shared connection or disabled same-thread protection.

Required contracts in [repository-lifecycle.md](contracts/repository-lifecycle.md):

- Verify acknowledged business-table INSERT precedes Entity.create and Domain creation rules run before successful commit. Confirm actual natural/composite identities and reject duplicate identities through database constraints without overwrites.
- Inject explicit Domain factory rejection and exception after INSERT; confirm real rollback leaves no committed Entity. Current typed factories need no invented rejecting business rule; a controlled factory seam exercises rollback responsibility.
- Verify newly created Entities/results remain local until enclosing commit is confirmed; failed operations expose no successful or reusable canceled creation result through returned values, callbacks, caches or exception payloads. Do not add tests for reservation/finalization/recovery or Entity lifetime states/revocation.
- Stage preceding/following writes in a UoW and prove Repository never independently commits. A failed creation must roll back the whole uncommitted operation.
- Exercise insertion failure, definite commit failure, uncertain commit, cleanup failure and confirmed response loss separately. Failed/uncertain transactions return no creation success. Uncertainty requires reconciliation through a later independent read/operational check; do not assume rollback/deletion is safe or delete/revert potentially committed complete state. Cleanup failure is technical failure rather than an unverified ordinary rejection; preserve an existing primary exception.
- Restore valid historical Entities without replaying admission; invalid saved state/version maps to DataIntegrityFailure and existing completion failure, not absence or invalid input.
- Verify Student creation starts at version 1, every successful conditional replacement advances it, stale writes return an explicit conflict, and confirmed rollback preserves committed details/version. No automatic retry or unconditional replacement is allowed.

Architecture checks need positive/violating fixtures for Repository-only production Entity creation/restoration and permitted Value Object boundary factories, including aliases. Structural checks do not prove semantic ordering, operation confinement or failure translation; retain contract tests and explicit review.

## Outside-In TDD and evidence

Add relevant acceptance cases before implementation, execute them and retain an actual expected behavioral failure. Missing imports/signatures, empty selection or environment failures are not behavioral Red. Guide cohesive inner-layer cycles with those acceptance outcomes; consider refactoring and retain relevant Green. No commit per cycle, intermediate snapshot, or separate no-refactor artifact is mandated.

After adding the relevant failing tests, the existing recorder can capture commands such as:

```bash
.venv/bin/python -m scripts.record student-version-replacement red .venv/bin/pytest tests/acceptance/test_student_details.py -q
# Implement the behavior; keep the same increment identity.
.venv/bin/python -m scripts.record student-version-replacement green .venv/bin/pytest tests/acceptance/test_student_details.py -q
```

The recorder already captures state-before/state-after, test identity, activity, timestamps and raw output. New v3.0.0 increments must require these associations and relevant acceptance/inner chronology. Preserve historical files unchanged; missing associations in old evidence are reported honestly and cannot satisfy a newly required increment. Use verification for behavior already passing, never manufacture Red.

## Mandatory final verification after implementation

```bash
bash scripts/check-quality.sh
# Inspect captured results and update evidence/reconciliation/review.json honestly.
.venv/bin/python -m scripts.assemble_evidence
.venv/bin/python -m scripts.check_evidence
```

Require all tests, exact scenario/variant inventory, complete Domain/Application statement-and-branch coverage, strict mypy, Ruff, Import Linter, architecture/contract tests, installed resources and real server tests against the final state. Only pure Protocol-signature modules qualify for the validated ellipsis exclusion; no business exclusions or changed-lines coverage gate.

Negative evidence fixtures must reject missing/skipped scenarios, absent/mismatched new-increment associations, unrelated Red/Green, overlapping/reversed execution, changed-during-run state, failing Green and stale/tampered final results. Preserve positive consolidated increment handling. Failed, skipped, blocked, missing or stale mandatory checks prevent completion. Planning documents and old green manifests do not certify implementation of these requirements.

## Planning verification and next workflow

This documentation update is checked for links, scenario coverage, consistent contract names and absence of unresolved placeholders. It does not execute the future behavior or rewrite evidence. Next run $speckit-tasks to reassess remaining implementation work from the current source and this design; keep historical completed tasks/history intact.
