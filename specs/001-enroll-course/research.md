# Research: Constitution v3.0.0 and saved-version replacement

**Date**: 2026-10-22
**Baseline**: Current [specification](spec.md), effective [constitution](../../.specify/memory/constitution.md), current source, and [ADR-0001](adr/0001-entity-lifecycle-and-student-revisions.md). This supersedes the v2.3.1 design assumptions in the preceding revision; Git and retained evidence preserve that history.

## Flagged uncertainties and amendments

| Flag | Unclear or outdated point | Amendment and status |
|---|---|---|
| R1 | ADR-0001 adds mechanisms beyond the required observable guarantees | Revise the existing ADR: use business-table INSERT confirmation and operation confinement, removing reservations and Entity handles. Resolved under the user revision instructions. |
| R2 | The old plan says Application constructs complete entities before saving | Repository confirms natural/composite identities through acknowledged uncommitted INSERTs into business tables before Domain construction. Application passes validated requests. Resolved. |
| R3 | Pending Entity references could escape a failed creation operation | Keep new Entities/results local until commit; prohibit publication/caching/callback or exception-payload escape and discard pending references on failure. Domain has no transaction tracking. Resolved. |
| R4 | The spec requires versions but leaves representation and host retrieval to planning | Positive integer SavedVersion, atomic StudentSnapshot read, required expected_version on replace, initial 1 and strictly advancing committed replacements. Resolved. |
| R5 | Mixed-invalid version/mode/existence cases lack a full technical ordering | IDs → name → email → mode → replacement version validity → target existence → Domain outdated-version check → Domain email policy. Resolved; no new business-rejection order in enrollment. |
| R6 | Legacy schema and direct provisioning do not account for saved versions | Refuse incompatible existing schemas before mutation, no automatic migration; new Student edits use conditional host operation, with schema guard for revision advancement. Resolved. |
| R7 | Old plan describes recorder associations and typed factories as wholly unbuilt | Those already exist. Retain and extend them; new-increment validation and production lifecycle restrictions still need work. Resolved by source inspection. |
| R8 | Old inventory/guide ends at enrollment 15 and Student 10, sometimes only seven Student families | Require all 19 enrollment and 17 Student families plus every existing variant. Current tests are not proof of newly specified behavior. Resolved. |
| R9 | Rollback wording could be read as undoing a commit with a lost acknowledgment | Distinguish uncommitted failure from uncertain/confirmed commit; discard unpublished results and return technical failure requiring reconciliation without destructive compensation. Already specified; carried through all contracts. Resolved. |
| R10 | Snapshot version is typed, but raw host commands require an integer | Send snapshot.saved_version.value at the raw boundary, then validate into SavedVersion for Repository Ports. Read snapshots commit, then close, before external return. Resolved. |
| R11 | Preserving a pending ordinary outcome could conceal rollback/close failure | Preserve propagating exceptions, but report StorageFailure over pending ordinary results if cleanup fails. Keep pending results unavailable and do not claim verified transaction termination without evidence. Resolved. |
| R12 | Entity-level transaction state adds unnecessary coupling | Remove handles and Entity lifecycle tracking. Application/UoW controls commit, cleanup and result exposure without a new lifecycle abstraction. Resolved. |
| R13 | Enrollment must reject corrupt saved versions but has no update/version policy | Validate saved_version during every Student restoration, including enrollment reads, without introducing Student version comparison/advancement into enrollment. Resolved. |

No unresolved implementation-planning marker remains. No additional user business decision was inferred: the recorded option B is the authority for rejecting outdated replacement. Representation/mechanism choices are feature design decisions.

## 1. Retain the stack and boundary isolation

**Decision**: Keep Python 3.12, Flask, graphql-core, Waitress, SQLite, pytest and the existing quality tools/lockfile. Keep the two declared acceptance boundaries: HTTP GraphQL enrollment and trusted Python Student integration.

**Rationale**: The requirements add lifecycle/concurrency guarantees, not a new transport, deployment model or dependency need. Domain remains framework-free; Application owns orchestration/Ports; adapters perform boundary conversion and persistence mechanics.

**Alternatives considered**: ORM, external database, asynchronous service rewrite, or a management endpoint would expand scope without resolving a required behavior more directly.

## 2. Identity confirmation before normal Entity creation

**Decision**: Within the enclosing BEGIN IMMEDIATE transaction, Repository INSERTs supplied state into the actual business table, obtains the acknowledged natural/composite identity, then invokes Entity.create with validated Domain values. Domain rejection or technical failure rolls back uncommitted changes. Application alone coordinates the enclosing commit; Repository never commits independently.

**Rationale**: Constitution II and FR-015 allow confirmation through association with stored state or reservation. The first option suffices: existing primary-key/unique constraints protect real identities, while transaction rollback removes rejected creations. An inserted row is intermediate persistence state until Domain accepts it; storage constraints never replace Domain rules. No dedicated reservation table, CreationData or ID generator Port is needed.

**Alternatives considered**: A dedicated reservation protocol duplicates the existing identity namespace. Local ID generation alone is not confirmation. Repository-owned commits break the enclosing transaction. INSERT OR REPLACE can delete an existing row and must not implement creation.

**Sources**: [SQLite constraints](https://www.sqlite.org/lang_createtable.html#constraints), [transactions](https://www.sqlite.org/lang_transaction.html) and [constraint conflict handling](https://www.sqlite.org/lang_conflict.html). SQLite's default constraint failure can abort a statement while preserving prior transaction changes, so the enclosing operation must explicitly roll back after rejection/failure. INSERT-before-factory is this project's design choice under the constitution, not a SQLite requirement.

## 3. Operation confinement and restoration

**Decision**: New Entities stay inside the creation operation until successful enclosing commit. Do not publish/cache them or pass them through callbacks/exception payloads before that point. Discard pending results after failure so canceled Entities are unavailable for further business use. Remove Entity lifetime handles and Entity-level transaction tracking. Restore saved identities via Entity.reconstitute and persisted-state invariants without replaying creation-only rules.

**Rationale**: Constitution II and FR-016 prescribe exposure/cancellation guarantees, not revocable Entity handles. Enforcing ownership of pending results at the operation boundary satisfies those guarantees while Domain remains independent of persistence status. A Domain Entity cannot determine whether an external commit succeeded.

**Alternatives considered**: Active/committed/revoked handles add an unnecessary lifecycle abstraction; ORM sessions or callbacks inside Domain violate isolation. Allowing references to escape and merely relabeling a failed result is insufficient; boundary tests/review must verify confinement. Absolute constructor privacy is unnecessary; supported API checks remain required.

## 4. Student snapshots and versions

**Decision**: Domain SavedVersion accepts strict integer input in 1..9,223,372,036,854,775,807; reject bool, strings, floats, zero, negatives and missing input. Host StudentSnapshot combines a persisted Student and saved-version metadata in one read. Creation establishes 1. Repository replacement atomically matches identity+expected version, writes all fields, and increments version once; identical details still increment. SQLite signed-64 exhaustion is technical failure, never wraparound or stale success.

**Rationale**: The user chose conflict rejection rather than overwrite. Revisions distinguish committed states even when field values later return to old values. Snapshot is semantically necessary concurrency metadata and does not change StudentId equality/hash or introduce audit history.

**Alternatives considered**: Timestamp/hash tokens can repeat or fail to advance on no-op writes. Silent reload/retry and unconditional old clients violate FR-018. A public management read endpoint is outside scope.

**Sources**: [SQLite RETURNING](https://www.sqlite.org/lang_returning.html) confirms that affected-row values can be returned without an extra query, but returned values alone do not prove commit. Use the existing sqlite3 cursor rowcount plus a same-transaction SELECT if avoiding a minimum SQLite RETURNING requirement; consume/close cursors before commit. No new SQLite version prerequisite is introduced by this design.

## 5. Atomic conditional update and Domain ownership

**Decision**: Application sequences existence, Domain version comparison, and Domain email policy. Repository owns the guarded UPDATE and invokes a controlled Domain Student detail transition on the existing confirmed identity before writing. Its defensive zero-row result remains an explicit outdated-version outcome, not a success. Application does not recompute Domain predicates or construct replacement Students.

**Rationale**: BEGIN IMMEDIATE prevents competing writers between the ordered read and write in this adapter; matching the version in SQL additionally makes the expected version part of the write contract. A successful update is still pending until commit. No-op updates advance and report a new version.

**Alternatives considered**: A separate unlocked check then update loses protection. DELETE/INSERT replacement risks referential semantics. Checking email before version violates the approved first-match behavior for stale input.

## 6. Compatibility and direct writes

**Decision**: Fresh schema explicitly stores initial version 1, strict integer/bounds constraints and an update guard requiring exactly OLD.saved_version+1. Inspect all required schema features before modifying an existing database; refuse incompatible schemas unchanged. No migration/backfill runs here.

**Rationale**: Existing supported direct Student update scripts otherwise leave tokens unchanged and defeat stale-write protection. Host callers must use conditional replacement. A schema guard protects monotonic advancement for any accepted SQL UPDATE, while expected-version intent still belongs to the supported command contract.

**Alternatives considered**: Silently accepting absent versions, automatically assigning versions to old data, or claiming raw database access is a security boundary would weaken approved requirements.

**Sources**: [SQLite CREATE TRIGGER](https://www.sqlite.org/lang_createtrigger.html) provides conditional rejection via RAISE. Use a validation-only guard, not a trigger that mutates the row being updated; the latter has documented BEFORE-trigger hazards.

## 7. Failure and commit semantics

**Decision**: Explicit factory rejection, exception or persistence failure after INSERT rolls back the enclosing operation's uncommitted changes and discards pending results. Recognized driver faults translate to Core StorageFailure/DataIntegrityFailure; programming errors retain their exception path. Failed/uncertain transactions return no successful creation result. Uncertain commit is technical failure requiring reconciliation through a later independent read/operational check, without assuming rollback/deletion is safe. Never delete/revert possibly committed complete records. Confirmed commit survives response loss. Student stale writes are never automatically replayed; enrollment retains its existing one-replay pair-conflict policy.

**Rationale**: Rollback of known uncommitted state differs from destructive compensation after possible commit. Neither an in-memory Entity nor a returned SQL row proves commit. Cleanup failure cannot be hidden behind a pending ordinary rejection; preserve an existing primary exception with secondary diagnostics.

**Alternatives considered**: Treating any commit exception as proof of rollback, deleting an uncertain creation, or retrying the write could corrupt or duplicate committed work.

**Sources**: [Python 3.12 sqlite3 transaction control](https://docs.python.org/3.12/library/sqlite3.html#transaction-control-via-the-autocommit-attribute) states connection commit/rollback do nothing with autocommit=True; explicit SQL controls this design. [SQLite transactions](https://www.sqlite.org/lang_transaction.html) documents commit failure and active-transaction behavior. Rollback only a transaction known to remain active and uncommitted; do not infer that state from an exception alone.

## 8. Current source and evidence assessment

**Decision**: Preserve working typed factories, separate restoration, Unicode semantics, integrity mapping, source digest capture and recorded test/activity association. Plan the genuinely remaining Repository/version and validation/inventory changes.

**Rationale**: Current Application still invokes Student.create/Enrollment.create, Student save overwrites without a version, and schema has no saved_version. Existing recorder already captures implementation state before/after execution, activity and test identity. The validator retains historical compatibility; new required increments need strict association so that path cannot certify new v3 work.

**Alternatives considered**: Re-running completed work as if missing, fabricating earlier Red runs, weakening coverage, or rewriting historical outputs would misrepresent evidence. Architecture import checks alone cannot prove identity confirmation, atomicity or commit exposure semantics.

## 9. Design verification disposition

Pre-design and post-design constitutional gates pass for the proposed design only. Validate local links, requirement/scenario mapping, cross-contract consistency, current source-gap descriptions and absence of unresolved markers. Implementation remains pending and must use acceptance-guided Outside-In TDD, real SQLite fault/race tests, strict static checks and final current-state evidence. Task generation is the next workflow.
