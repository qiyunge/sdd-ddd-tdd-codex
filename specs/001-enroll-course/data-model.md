# Data Model: Repository lifecycle and saved Student versions

**Baseline**: [spec.md](spec.md), Constitution v3.0.0, [ADR-0001](adr/0001-entity-lifecycle-and-student-revisions.md). This is the target design; source/schema migration is pending.

## Domain values and identity

StudentId, ProgrammeId, CourseId and SubjectId are exact nonempty strings; whitespace is not trimmed and case is not folded. `.create(raw)` returns a typed value or InvalidIdentifier; `.reconstitute(raw)` returns a typed value or InvalidPersistedState. VerifiedIdentity is a nonpersisted Value Object containing a validated SubjectId after trusted verification, not evidence of Student existence.

StudentName and StudentEmail require actual strings with a non-whitespace character under the existing Python 3.12 text rules. Preserve original text. StudentEmail equality/hash uses complete `str.casefold()` output, including multi-character expansions; whitespace, Unicode composition, dots and plus tags are not normalized. Names are not unique. Field input failure returns InvalidStudentDetails(field); invalid stored text is an integrity failure.

SavedVersion is a Domain Value Object containing an integer from 1 through 9,223,372,036,854,775,807. Bool, missing input, strings, floats and out-of-range values are invalid; no coercion. Normal input returns InvalidSavedVersion, restoration returns InvalidPersistedState. Reaching the maximum on a requested replacement is a technical persistence limitation: no update, no version wrap/reuse. A saved version is concurrency metadata, not an Entity identity.

## Entities and snapshots

| Type | Identity | State and invariants |
|---|---|---|
| Student | StudentId | ProgrammeId, nonblank StudentName/StudentEmail; immutable identity, equality/hash by StudentId only. Programme existence is not a construction/restoration invariant. Global email availability is a contextual Domain policy plus atomic write guard. |
| Programme | ProgrammeId | Valid confirmed identity; existing prerequisite, no management use case added. |
| Course | CourseId | Valid confirmed identity; shared by multiple programmes. |
| ProgrammeCourseOffering | (ProgrammeId, CourseId) | Both confirmed typed components; represents a persisted offering relationship. |
| Enrollment | (StudentId, CourseId) | Unique confirmed pair; new admission requires approved prerequisite/duplicate/offering policy sequence. |
| StudentSnapshot | Not an Entity | Immutable Application result containing a Repository-issued Student and SavedVersion from one saved row/atomic operation. Its wrapper carries necessary concurrency metadata, not duplicate Domain fields. |

Entities contain Domain state and invariants, without transaction status or persistence lifecycle handles. Persistence acknowledgment of the inserted/stored identity confirms it; a typed ID alone does not. Newly constructed Entities stay inside the creation operation until commit is confirmed.

## Logical schema

Existing business tables retain their business keys and relationships:

- `programmes(programme_id)` and `courses(course_id)` retain exact text primary keys.
- `students(student_id, programme_id, name, email, saved_version)` retains StudentId primary key, required text constraints, and the global unique `students_email_key` expression index backed by Domain email comparison. A usable programme_id need not reference an existing Programme, preserving missing-programme enrollment behavior.
- `programme_course_offerings(programme_id, course_id)` retains its composite primary key and existing foreign keys.
- `enrollments(student_id, course_id)` retains its composite primary key and existing foreign keys; no term/year exception or additional identity is added.

Student saved_version is NOT NULL INTEGER with strict SQLite `typeof(...)=integer` and positive signed-64 range. Repositories insert 1 explicitly for fresh Students; no silent version assignment is applied to existing schemas. A validation-only BEFORE UPDATE guard rejects any Student update whose new saved_version is not exactly the previous value plus one, including unchanged-detail writes. Exhaustion cannot pass through floating-point promotion. The guard does not mutate rows or establish caller intent; supported edits still require the expected-version host contract.

SQLite functions `required_text` and `email_key` are registered on every configured connection and delegate to Domain rules. Unconfigured writes fail closed; no independent ASCII key or stored caller-forgeable email key is added.

## Confirmation and creation transitions

```text
validated request values
  -> enclosing BEGIN IMMEDIATE
  -> business-table INSERT acknowledged; actual natural/composite identity obtained
  -> Domain Entity.create with confirmed identity and validated values
  -> Domain acceptance; pending Entity kept within creation operation
  -> enclosing Application COMMIT confirmed
  -> successful Entity or StudentSnapshot result
```

Application owns the transaction; Repository owns persistence confirmation and Entity construction. Primary-key/unique constraints reject duplicate identities. Obtain the inserted identity through a same-transaction read (or fully consumed RETURNING if supported); retain separate components for composite keys. This does not require a new SQLite version or generated business identity.

INSERT precedes Domain construction, but its state stays uncommitted and rollback-capable. Entity.create enforces creation rules before successful commit. Any explicit Domain rejection, exception or persistence failure causes rollback of the enclosing operation's uncommitted writes. Repository never commits. Do not use INSERT OR REPLACE or salvage partial work into a commit.

Pending Entities must not leave the operation through results, caches, callbacks or exception payloads. On failure discard pending references and make no canceled Entity available for later business use. Domain Entities have no transaction status, revocation API or lifetime handle. There is no reservation table or allocation/finalization/recovery protocol.

## Restoration

```text
persisted row -> validated persisted Value Objects
  -> Entity.reconstitute(persisted identity, state)
  -> valid Entity; no creation-only eligibility replay
```

Missing rows remain None. Every Student restoration validates its persisted saved_version, including enrollment reads returning only Student; that read need not expose the revision. Invalid stored identity, details, version or entity invariant becomes Domain InvalidPersistedState, then Core DataIntegrityFailure(StorageFailure), then the existing sanitized completion failure. Never turn corruption into absence or invalid user input.

A valid saved Enrollment can be read after membership/offerings change; a Student can be restored with a usable programme identity whose Programme is absent. Do not replay email availability during restoration. Snapshots contain no lazy reads or persistence resources. Stale snapshots cannot authorize replacement without the matching saved version.

## Conditional Student replacement

1. The host obtains details plus saved version through get_student. The returned snapshot is committed/connection-free before external return.
2. The host submits mode=replace, student_id, programme_id, name, email and raw expected_version=snapshot.saved_version.value from the state originally read; Application validates it into SavedVersion for Repository Ports.
3. Application validates fields in approved order, validates mode, then replacement-version representation. Invalid input stops before persistence.
4. Under BEGIN IMMEDIATE, Repository reads the target snapshot. Absence returns StudentNotFound. Domain compares expected/current version; mismatch returns OutdatedVersion before email policy.
5. Domain email policy compares ownership by StudentId. If allowed, Repository invokes a controlled Student.replace_details transition on the existing confirmed identity; it does not recreate a new business identity or call reconstitution on arbitrary unsaved state.
6. Repository updates the full details and saved_version+1 with predicates on StudentId and expected_version. It must affect one row. A defensive zero-row result is an explicit outdated-version outcome; this adapter cannot legitimately lose the row between its checks under the writer lock.
7. Application commits once, then returns the new StudentSnapshot. Rejection or confirmed rollback leaves the committed version unchanged. Cleanup failure is technical failure and does not justify reporting success.

All updates based on one saved version compete for that version. With persistence available and otherwise valid input, exactly one succeeds and the other is outdated. A caller must reload before retry; Application must not automatically refresh the expected version. Even identical-detail replacement consumes a new saved version; old field values restored later cannot revive an old token. There is no automatic merge or version history API.

## Failures, compatibility and direct provisioning

Confirmed rollback after a pre-commit failure preserves prior committed details/version and removes new uncommitted state. Failed or uncertain transactions expose no successful creation result. Uncertain commit requires reconciliation through a later independent read/operational check; do not assume rollback/deletion is safe or delete/revert possibly committed complete state. Rollback applies only to a transaction known to remain active and uncommitted. Confirmed commit survives response loss; retrying a replacement with the old version returns OutdatedVersion if the target still exists. Enrollment retries continue following FR-009, not the Student version policy.

Inspect existing schema compatibility before mutation, including saved_version column/constraints, revision guard and stored-version validity. Refuse incompatible/legacy databases unchanged; hosts arrange an external audited migration or fresh provisioning. Compatible initialization is idempotent. Do not weaken constraints to fabricate corrupt/missing-record test fixtures.

Fresh provisioning uses Repository creation helpers for complete Entity instances. Direct SQL may establish valid prerequisite persisted state using configured connections, but it must not construct business Entity instances outside Repository. Existing Student edits must use conditional host replacement; unconditional SQL update is unsupported even when a version-advancement trigger could accept its arithmetic.

## Verification mapping

FR-015–FR-017 map to US1 16–18, US2 11–13, SC-008–SC-010, plus real Repository atomicity and commit-boundary tests. FR-014 maps to US1 19 and existing invalid-input HTTP cases. FR-018 maps to US2 14–17, SC-007/SC-011, and snapshot/version/conditional-write contract tests. Preserve all original acceptance variants, Domain equality/hash checks, whole-Core coverage and historical evidence; see [quickstart](quickstart.md).
