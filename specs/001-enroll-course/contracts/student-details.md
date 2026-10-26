# Trusted Student Snapshot and Conditional Replacement Contract

**Scope**: Host-only Python integration under Constitution v3.0.0, FR-011–FR-013 and FR-018. No new HTTP/GraphQL management endpoint, email login, identity-provider behavior, or enrollment reason is added. See [data model](../data-model.md) and [Repository contract](repository-lifecycle.md).

## Operations and command shape

The planned Application integration retains `save_student(command, sessions)` and adds `get_student(student_id, sessions)` in the Student integration module. get_student accepts raw identity input, validates it through StudentId.create, reads one saved snapshot, commits, then closes its transaction before returning that snapshot or the existing missing/technical outcome. It adds no list/search or public read endpoint.

save_student command fields:

| Field | Create | Replace |
|---|---|---|
| mode | Literal create | Literal replace |
| student_id | Required raw exact nonempty string | Required raw exact nonempty string |
| programme_id | Required usable ID; programme existence not required | Required complete replacement value |
| name, email | Required nonblank strings | Required complete replacement values |
| expected_version | Not a creation precondition; absent normally, supplied value is ignored for create | Mandatory raw snapshot.saved_version.value from the state originally read; integer in 1..9,223,372,036,854,775,807, no bool/coercion |

This is a full replacement, not a patch. Trusted hosts must adopt the saved-version contract; a missing expected_version on replace is invalid input, never an unconditional compatibility fallback. Choosing create explicitly continues to return already-exists for an existing Student rather than replacing it.

## Snapshot and outcomes

StudentSnapshot is a frozen Application result with `student: Student` and `saved_version: SavedVersion`. Details and version are obtained from the same persisted row or successful atomic change. All successful external snapshots contain a committed Entity and have no lazy reads, live connection, or framework types. Versions are concurrency metadata; StudentId equality/hash is unchanged.

| Result | Meaning and mutation guarantee |
|---|---|
| StudentSnapshot | Read completed or create/replace committed; includes the saved version |
| InvalidIdentifier | Unusable StudentId/ProgrammeId; no write |
| InvalidStudentDetails(field) | Required name/email or mode input invalid; no write, no sensitive field echo |
| InvalidSavedVersion | Missing/unusable replacement version; no write |
| OutdatedVersion | Supplied version differs from the current committed version; no overwrite/version change, caller reloads |
| EmailConflict | Another Student owns the full Unicode comparison key; no change |
| StudentAlreadyExists | Create targets an existing identity; current record/version preserved |
| StudentNotFound | Read/replace targets an absent identity; no Student created |
| StudentStorageFailure | Known open/lock/read/write/commit/schema/integrity failure; no raw driver diagnostics |

InvalidSavedVersion and OutdatedVersion are explicit Domain outcomes; keep persistence technical observations separate as described in the Repository contract. Unexpected programming/contract errors propagate to the host error boundary and are sanitized there, not mislabeled as invalid details, stale input, email conflict or absence.

## Ordered save processing

1. Validate StudentId, ProgrammeId, StudentName and StudentEmail with Domain Value Object factories, stopping in that order. Preserve supplied text, Unicode whitespace rules and complete-address full Unicode case folding. No Entity is constructed yet.
2. Validate mode as create/replace, retaining the existing position after the four fields. For replace, validate required expected_version next; invalid version stops before any persistence lookup. Create has no version precondition.
3. Open a fresh worker-owned Student UoW, register Domain-backed SQL functions and execute BEGIN IMMEDIATE before reads.
4. Read the target snapshot. For create, an existing identity returns StudentAlreadyExists. For replace, absence returns StudentNotFound before any stale/email policy. These are not email conflicts.
5. For replace, invoke the pure Domain version policy on expected/current SavedVersion. A mismatch returns OutdatedVersion before email availability; no automatic reload, merge or write retry follows.
6. Read the owner of the complete email comparison key; Domain email policy excludes self by StudentId and returns EmailConflict for another owner. Application branches on the Domain outcome without recomputing its predicate.
7. Invoke Repository create_student or replace_student with the validated values. New creation INSERTs state with initial version 1, obtains the confirmed StudentId from inserted state, then invokes Domain Student.create before the enclosing commit. Replacement invokes a controlled Domain transition on the persisted identity and performs the identity/version guarded UPDATE, writing version+1. Repository never commits.
8. Translate precise EmailKeyConflict or defensive VersionConflict observations to their expected outcomes; unrelated driver failures retain technical classification. Explicit Domain rejection or exception after persistence changes rolls back the enclosing operation's uncommitted changes.
9. Application commits the complete operation, then returns StudentSnapshot. Every committed replacement advances version, even if every supplied detail equals its current value. Rejected/rolled-back writes do not advance it. Maximum-version exhaustion is a technical failure without write, not wraparound.

Keep new Entities and pending snapshots inside the operation until commit is confirmed. Do not publish/cache them or expose them via callbacks or exception payloads. On rejection/error, discard pending references and roll back known active, uncommitted changes; canceled Entities remain unavailable for later business use. Entities have no transaction status or lifecycle handles. If cleanup fails while an ordinary result is pending, surface StudentStorageFailure and retain that result diagnostically; do not report a normal rejection with unconfirmed transaction termination. An already-propagating unexpected exception remains primary with cleanup diagnostics. Definite failure preserves the current committed details/version. On uncertain commit return StudentStorageFailure requiring reconciliation through a later independent read/operational check. Do not assume rollback/deletion is safe or delete/revert potentially committed complete state. A confirmed commit survives response loss; retrying with the old version is outdated. Read and apply current details/version only when the caller deliberately reloads and submits a new request.

## Concurrent and mixed-failure behavior

- Two otherwise valid replacements for one Student based on the same saved version produce one committed snapshot and one OutdatedVersion when persistence is available. Never mix fields, overwrite the winner with stale intent, or restore the loser's earlier view.
- Two different Students claiming one unused caseless email still produce one committed success and one EmailConflict. This rule does not turn two updates to one Student into competing email owners.
- Invalid name/email precedes invalid version. Invalid/missing expected_version precedes target lookup. A usable version with a missing target returns StudentNotFound. Outdated version precedes another Student's email conflict.
- Reload/retry can succeed only against the then-current saved version and all other validity/availability checks. An intervening update can produce another outdated conflict.
- Replacing A with B and later restoring A still advances the version; neither hashes of details nor timestamps may allow an old token to become valid again.

## Storage compatibility and host obligations

Use the existing local SQLite topology, configured Domain-backed comparison functions, global email index and existing identity relationships. Add saved_version representation/advancement constraints as specified in the data model; identity confirmation uses existing business-table primary-key/unique constraints and transactions. Compatible initialization remains idempotent. Refuse old/incompatible schemas before any mutation; migration/backfill is external and no default details or old-row versions are fabricated.

Fresh Student creation assigns version 1 explicitly. Direct unconditional updates to existing Students are not supported; use this conditional host integration. The database guard requires every accepted Student update to advance version by one, but arbitrary raw SQL is not an authorization boundary or proof of caller-supplied expected_version. Update host provisioning helpers and fixtures accordingly.

## Acceptance and verification

Preserve every original Student acceptance variant, including Unicode case expansion, composition non-equivalence and significant spaces. All replacement fixtures/helpers must obtain and explicitly supply a saved version; race/stale tests must not auto-refresh that version.

US2 1–10 continue to cover details, uniqueness, existence and first-invalid-field behavior. US2 11–13 cover committed identity/state, atomic creation failure and failed replacement preservation. US2 14–17 cover competing same-version replacement, deliberate reload/retry, missing version and lost/uncertain commit response. Require exact identities student-details-1 through student-details-17 plus all original parameterized cases.

Add focused contracts for snapshot consistency/no lazy reads, version input edge cases including bool/range, unchanged-detail advancement, maximum-version exhaustion, value restoration without token reuse, stale+email conflict, absent+version cases, corrupt persisted versions, SQL guard and schema refusal. Real Repository tests prove no premature commit, INSERT-based identity confirmation, Domain-rejection rollback, duplicate-identity rejection and success only after commit, beyond what dependency checks can prove. New behavioral increments require state-associated Red/Green evidence and final whole-Core coverage/static gates.
