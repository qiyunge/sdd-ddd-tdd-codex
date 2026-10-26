# Domain Construction, Transition and Reconstitution Contract

**Baseline**: [spec](../spec.md) under Constitution v3.0.0 and [ADR-0001](../adr/0001-entity-lifecycle-and-student-revisions.md). This is the target internal contract; Repository/version implementation is pending.

## Supported Value Object creation

| Models | Normal `.create` input | Explicit expected outcome |
|---|---|---|
| StudentId, ProgrammeId, CourseId, SubjectId | raw object | Typed exact nonempty string or InvalidIdentifier |
| StudentName, StudentEmail | raw object | Typed actual string with a non-whitespace character or InvalidStudentDetails(field); preserve original text |
| SavedVersion | raw object | Typed integer in 1..9,223,372,036,854,775,807, rejecting bool/coercion, or InvalidSavedVersion |
| VerifiedIdentity | validated SubjectId after trusted verification | Trusted identity; no Student-existence assertion |

Values own their invariants regardless of caller. Adapters and Application may use these supported factories for technical adaptation; no mandatory Application gateway or redundant DTO is required. Value Objects use a single validated `.create(raw)` path when input validation and persisted-state invariants are identical, as they are for all persisted values in this feature. Persistence translates invalid factory outcomes into DataIntegrityFailure for stored values; it does not duplicate validation or require a Value Object `.reconstitute(raw)` API. VerifiedIdentity is nonpersisted in this feature.

## Complete Entity factories

All complete Entities expose `.create` and `.reconstitute`; only persistence implementations of Core-owned Repository Ports invoke these APIs in production. Internal constructors are not alternative public construction paths. Isolated Domain factory tests may supply valid identities without a database; they do not establish confirmation.

| Entity | `.create` components | Identity confirmation |
|---|---|---|
| Student | StudentId, ProgrammeId, StudentName, StudentEmail | Acknowledged Student INSERT; identity obtained from inserted state |
| Programme / Course | matching typed ID | Acknowledged INSERT of that key into its business table |
| ProgrammeCourseOffering | ProgrammeId, CourseId | Acknowledged offering INSERT with that pair |
| Enrollment | StudentId, CourseId | Acknowledged enrollment INSERT with that pair, after approved Domain policies |

Repository coordinates the acknowledgment before calling Domain. Domain receives validated components and enforces applicable entity-level invariants without querying storage or treating syntactic validity as confirmation. Expected creation rejection remains an explicit Domain outcome; internal misuse may raise contract exceptions. A factory with no expected rejecting branch for valid typed inputs need not invent a business rejection.

The lifecycle order and rollback responsibilities are defined in [Repository contract](repository-lifecycle.md). Application passes validated requests and never calls complete Entity factories or passes a newly created complete Entity to an add/save port.

## Student detail transition and version policy

Student.replace_details accepts validated ProgrammeId, StudentName and StudentEmail on a Repository-issued Student and enforces applicable transition invariants while retaining StudentId. Repository invokes this controlled transition for full replacement, not restoration of arbitrary requested state. Versions are held in the Application StudentSnapshot alongside Student; Student equality/hash remain StudentId-based.

Domain owns a pure version policy comparing SavedVersion expected/current and returning OutdatedVersion or permission to continue. Application sequences that policy after target existence and before email availability, without duplicating its predicate. Domain also owns complete-address email comparison and the contextual email-availability policy. Repository supplies the observed owner and actual saved version; SQL conditional predicates provide persistence enforcement, not replacement business decisions.

No Student mutation, metadata wrapper, or factory invocation creates a new business identity. Missing programme is not a Student creation/transition invariant; no new email syntax or provider equivalence is introduced.

## Creation operation boundary

Domain Entities and their factories MUST NOT depend on transaction status, sessions or persistence lifecycle handles. Repository inserts the supplied state before calling Entity.create; Domain still owns creation-specific invariants. All such writes remain uncommitted until the enclosing Application-owned operation accepts Domain creation and commits successfully.

Keep new Entities local to that operation until commit is confirmed. No publication through callbacks, caches, results, exception payloads or external effects is allowed beforehand. On failure discard pending Entity/result references; canceled creations remain unavailable for further business use. Enforce this through orchestration and boundary contracts, without Entity-level transaction tracking or revocation APIs.

Explicit Domain rejection or exception after INSERT requires rollback of the enclosing transaction's uncommitted writes. Failed/uncertain transactions never return creation success. Uncertain commit is technical failure requiring reconciliation, without assuming rollback or deletion is safe. See [Repository contract](repository-lifecycle.md).

## Persistence reconstitution

Persisted identifiers/details/versions are decoded through their shared validated `.create` factories. Validate Student saved-version metadata on every Student restoration, including enrollment reads which return only the Entity; this does not add version comparison/advancement to enrollment. Repository then calls Entity.reconstitute with the identity obtained from the actual row, validated components. Entity creation and restoration retain distinct APIs because their lifecycle semantics differ.

| Restored Entity | Saved-state invariants | Creation-only rules not replayed |
|---|---|---|
| Student | Valid StudentId/ProgrammeId, nonblank name/email, unchanged identity/text semantics | Contextual email availability; no added programme-existence requirement |
| Programme / Course | Valid typed persisted identity | Enrollment eligibility |
| ProgrammeCourseOffering | Valid persisted pair | Enrollment admission |
| Enrollment | Valid persisted student-course pair | Current membership/offering/duplicate-admission policy |

Invalid values return InvalidIdentifier, InvalidStudentDetails or InvalidSavedVersion; invalid Entity state returns InvalidPersistedState. Persistence translates these outcomes to Core DataIntegrityFailure(StorageFailure). Application returns the existing PERSISTENCE_FAILURE/StudentStorageFailure rather than absence, invalid request, email conflict or a new FR-009 rejection. Unexpected programming errors retain their exception path and sanitized outer handling.

## Required checks

- Inventory every Value Object/Entity factory; reject unsupported direct/aliased Entity construction in production and allow supported Value Object boundary use.
- Restrict production Entity create/reconstitute call sites to persistence Repository implementations, with allowed and violating architecture fixtures.
- Verify invariant outcomes, Unicode equality/hash, identity preservation and controlled transitions behaviorally.
- With real SQLite, verify INSERT acknowledgment before factory invocation, Domain rules before successful commit, duplicate-identity rejection, rollback after explicit Domain outcome and exception, no committed rejected Entity, no partial Repository commit, and success only after commit.
- Verify pending creation results remain inside the operation and failure exposes no successful or reusable canceled Entity. Uncertain commit requires technical failure and reconciliation without destructive compensation.
- Restore valid historical state without replaying admission; reject corrupt state without disguising it as a user/business outcome.
- Use an injected factory seam to exercise explicit rejection when currently valid typed input has no rejecting business case; do not invent requirements or weaken existing assertions.
