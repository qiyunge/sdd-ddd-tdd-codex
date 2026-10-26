# Repository and Unit-of-Work Contract

**Baseline**: Constitution v3.0.0; FR-015–FR-018; [ADR-0001](../adr/0001-entity-lifecycle-and-student-revisions.md). Target contract, implementation pending.

## Ownership and types

Application owns Repository/UoW Protocols and coordinates use-case policy sequencing and the enclosing commit. Persistence implements the Ports and coordinates SQL with Entity construction/restoration. Domain owns Entities, Value Objects and pure policy outcomes. Entities carry no transaction status or persistence lifecycle handles. No SQLite Connection/Row/Cursor/exception or framework type appears in Core contracts.

Repository accepts validated Domain values or requests containing them, never an Application-constructed complete Entity. It is the production entry point for complete Entity creation/restoration. StudentSnapshot is an immutable Application result carrying a Repository-issued Student plus SavedVersion from one saved state, not a new Entity or redundant copy of its fields.

## Port operations

| Operation | Input | Result inside enclosing operation |
|---|---|---|
| Enrollment UoW student/programme/course/enrollment/offering reads | Corresponding validated ID(s) | Restored valid Entity or None |
| Enrollment UoW create_enrollment | StudentId, CourseId | Pending Enrollment, precise PairConflict, or explicit applicable Domain creation rejection |
| Student UoW snapshot | StudentId | StudentSnapshot from one row or None |
| Student UoW email_owner | Complete Domain comparison key | Owner StudentId or None |
| Student UoW create_student | StudentId, ProgrammeId, StudentName, StudentEmail | Pending StudentSnapshot, StudentAlreadyExists observation, precise EmailKeyConflict, or applicable Domain creation rejection |
| Student UoW replace_student | Validated full details plus required SavedVersion expected_version | Pending StudentSnapshot, StudentNotFound observation, VersionConflict, precise EmailKeyConflict, or applicable Domain transition rejection |
| UoW commit | No business input | None only after acknowledged enclosing commit; never independently invoked by Repository operations |
| UoW rollback/close | No business input | Finish known uncommitted work/resources; preserve primary exceptions and surface cleanup failure over pending ordinary outcomes |

Pending creation/replacement results stay local to the use case until commit is confirmed. Application must not expose them as successful, cache them, publish callbacks containing them or allow canceled Entities to remain available for later business use. Failed operations discard pending Entity/result references. No Entity revocation or handle tracking is required.

StudentAlreadyExists/StudentNotFound observations map to existing Application results. VersionConflict means the guarded write did not match; Application translates it to Domain OutdatedVersion without duplicating the normal Domain comparison. EmailKeyConflict maps to Domain EmailConflict. Expected conflicts are returned values, not exceptions used for normal control flow.

Enrollment exposes no Student writes or version comparison/advancement. Student restoration still validates saved_version even when returning only Student. Trusted provisioning/test setup may create prerequisite Entities through the same Repository ordering; no management endpoint or Repository per Entity is required.

## Creation algorithm

1. Application validates supplied input through Domain Value Object factories, then invokes Repository within its use-case orchestration. Application does not generate Entity IDs.
2. Repository begins or participates in the enclosing transaction. This adapter's UoW starts explicit SQL BEGIN IMMEDIATE before use-case reads; identity verification precedes the transaction.
3. Repository performs an ordinary INSERT into the business table with supplied/derived natural or composite keys and validated state. New Student rows explicitly use saved_version=1. Successful INSERT acknowledges the identity/state association under database primary-key/unique constraints. Obtain the actual inserted identity through a same-transaction read or fully consumed RETURNING if supported; do not require a new SQLite version. Do not use INSERT OR REPLACE or ignore a failed insertion.
4. Repository invokes Entity.create with validated Domain values and the confirmed identity. INSERT is intermediate uncommitted persistence state; it does not substitute SQL/defaults for Domain creation rules.
5. Explicit Domain rejection, unexpected exception or persistence failure causes the entire enclosing operation's uncommitted changes to roll back. Return the appropriate explicit rejection or translate/propagate the technical exception. Do not catch failure and later commit another portion of the operation.
6. On acceptance, Repository returns a pending Entity/snapshot only to its enclosing use case, without committing. Application keeps it inside that operation.
7. Application commits once after the complete use case succeeds. Only acknowledged commit permits a successful external result or externally visible business effects. A failed or uncertain commit never returns creation success.

Use existing business-table keys; there is no identity reservation table, allocation/finalization/recovery protocol, CreationData, ID generator Port or Entity lifecycle abstraction. Duplicate Student identity maps precisely to StudentAlreadyExists, enrollment pair duplication to PairConflict, and email-key duplication to EmailKeyConflict. Unrelated constraints remain technical faults. Normal Application checks preserve rejection precedence; database constraints remain authoritative against duplicate writes.

## Restoration and conditional replacement

Read actual saved identity/state, decode persisted values and invoke Entity.reconstitute. Missing rows are None. Corruption becomes DataIntegrityFailure, not absence or invalid input. Do not replay creation-only enrollment/email-availability rules during restoration.

Student replacement preserves the approved sequence: validate StudentId, ProgrammeId, name, email, mode, then required expected_version; check target existence, Domain outdated-version policy, then Domain email policy. Application branches on Domain outcomes without reimplementing their predicates.

Repository invokes the controlled Student.replace_details transition on the confirmed existing identity before writing. Perform a full UPDATE guarded by StudentId and expected_version, advancing saved_version by exactly one in the same statement. No delete/reinsert, automatic retry, unconditional fallback or identity generation is allowed. Return Student and its new version from that same transaction; Application exposes the snapshot only after commit. Unchanged-detail replacements also advance; rejection or confirmed rollback leaves the committed version unchanged.

Under BEGIN IMMEDIATE, a post-check zero-row UPDATE is defensive VersionConflict, never success. Any future weaker-isolation adapter must distinguish missing target from version conflict without silently retrying. Unrelated SQL errors are StorageFailure, not guessed stale/email conflicts. Maximum-version exhaustion is technical failure without write or wraparound.

## Transaction outcomes and cleanup

| Event | Persistence/result rule |
|---|---|
| INSERT and Domain acceptance before commit | Keep pending Entity/snapshot inside the creation operation; no external success/effects |
| Acknowledged enclosing COMMIT | Successful result may leave the operation; materialized Entities have no lazy connection reads |
| Explicit rejection or pre-commit failure | Roll back the known active uncommitted operation, discard pending results; no committed rejected Entity or successful result |
| Rollback/close failure | Technical failure; do not claim verified termination. Preserve a propagating exception with cleanup diagnostics; replace a pending ordinary outcome with completion failure, retaining its context diagnostically |
| Commit outcome uncertain | Technical completion failure requiring later independent read/operational reconciliation; discard unpublished results, do not assume rollback/deletion is safe, and never delete/revert potentially committed complete state |
| Response/cleanup failure after confirmed commit | Do not compensate/delete durable state or pretend it rolled back |

Rollback applies only to a transaction known to remain active and uncommitted. An exception alone is not proof of rollback or failed commit. With Python 3.12 autocommit=True use explicit SQL BEGIN IMMEDIATE/COMMIT/ROLLBACK; Connection.commit()/rollback() are ineffective in that mode. Each worker owns its connection through close. Read-only get_student completes/closes its transaction before returning a materialized snapshot.

Storage/compatibility faults translate into documented Core StorageFailure categories; DataIntegrityFailure is a subtype. Application maps recognized faults to existing sanitized completion failures. Unexpected programming/contract errors propagate to the outer host/transport error boundary, never ordinary business rejection. Entities do not inspect transaction outcome. Keep failed-operation Entities out of result objects, caches, callbacks and exception payloads rather than trying to revoke them.

## Required real-persistence contracts

- Verify acknowledged INSERT of the actual identity precedes Entity.create and Domain creation rules execute before successful commit; retain exact natural/composite identities.
- Inject explicit factory rejection and exception after INSERT; confirm rollback leaves no committed Entity and failed creation returns no successful or reusable canceled result.
- Attempt duplicate identities and verify database constraint rejection without overwriting the existing record; check precise conflict translation.
- Stage preceding/following writes in a larger UoW and prove Repository does not independently commit; a rejected creation rolls back the entire uncommitted operation.
- Exercise insertion, definite commit and cleanup failures; confirm no failed transaction returns a successful creation result. Do not add tests for removed reservation or Entity-handle mechanisms.
- Restore valid state after creation-only eligibility changes; reject corrupt saved values/versions as integrity failures.
- Race same-version Student replacements and independent email claims using separate connections and bounded synchronization. Verify explicit stale conflict, version 1 creation, every successful replacement advancing, and rollback preserving committed details/version.
- Simulate uncertain commit and confirmed response loss separately. Require reconciliation without deletion, reversion or automatic write replay; a later read must not fabricate an earlier success response.
