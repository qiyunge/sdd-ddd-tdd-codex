# Domain Construction and Reconstitution Contract

**Baseline**: revised feature spec; proposed Constitution v2.1.0 delivery constraints.
Common API/error conventions are shared [D2/D3](../../../.specify/memory/architecture-decisions.md),
not independently defined by this feature. This is a planned internal contract;
current implementation migration is pending.

## Normal creation

| Models | Supported `.create` inputs | Applicable validity / outcome |
|---|---|---|
| StudentId, ProgrammeId, CourseId, SubjectId | raw object | Exact nonempty string; valid typed identifier or InvalidIdentifier |
| StudentName, StudentEmail | raw object | Actual string with a non-whitespace character; valid value or InvalidStudentDetails(field); preserve supplied text |
| VerifiedIdentity | validated SubjectId, supplied only after trusted verification | Valid identity; no Student-existence assertion or client verification flag |
| Student | StudentId, ProgrammeId, StudentName, StudentEmail | Typed nonblank details, immutable StudentId identity; no implied programme existence or global email-availability lookup |
| Programme | ProgrammeId | Typed identity; factory required despite no additional invariant |
| Course | CourseId | Typed identity; factory required despite no additional invariant |
| ProgrammeCourseOffering | ProgrammeId, CourseId | Both typed IDs; no extra eligibility or lookup |
| Enrollment | StudentId, CourseId | Typed immutable pair; Application reaches creation after existing Domain duplicate/eligibility policies |

The Identifier and RequiredText bases supply common invariant implementations; inherited
factories remain type-preserving. Domain outcome carriers are not substituted for business
models. Factories return models or applicable explicit expected creation failures; a typed
factory with no expected failing case need not invent one. Internal type-contract misuse
may raise; it is not ordinary raw-input validation. Internal constructors are unsupported
for Application, Adapters, hosts and ordinary fixtures, even if Python can access them.
No absolute constructor privacy mechanism is mandated.

For Student create/replace, Application first validates StudentId, ProgrammeId, StudentName,
then StudentEmail through value factories and branches on their outcomes before calling
Student.create with typed values. Preserve existing first-invalid-field behavior and mode
handling. Enrollment keeps verification -> target ID -> ownership -> course ID -> FR-009
prerequisite/policy sequencing; this migration introduces no new rejection step.

## Persistence reconstitution

Persisted identifier/text values expose `.reconstitute(raw)` returning the valid value or
Domain InvalidPersistedState. Persisted records expose `.reconstitute(typed components)`
returning the record or InvalidPersistedState for violated persisted entity invariants.
The same pure invariant predicates may be reused by both paths; reconstitution does not
call creation-only eligibility. VerifiedIdentity is not a persisted record in this feature.

| Restored record | Persisted invariants | Rules not replayed |
|---|---|---|
| Student | StudentId, ProgrammeId, nonblank name/email, unchanged spelling and identity semantics | Current contextual email availability; no new programme-existence condition |
| Programme / Course | Valid typed ID | Current enrollment eligibility |
| ProgrammeCourseOffering | Valid typed programme/course pair | Enrollment admission |
| Enrollment | Valid typed student/course pair | Current membership, programme offering or duplicate-admission policy |

Database uniqueness constraints and Domain policy still govern writes; restoration does not
waive stored integrity. Missing rows remain None. Persistence Adapters may call restoration
directly through their Core-owned Port implementations, without an Application gateway.
Invalid persisted primitives or records become Domain InvalidPersistedState, then Core-owned
DataIntegrityFailure(StorageFailure). Application preserves PERSISTENCE_FAILURE or the host
StudentStorageFailure result, with the integrity category available only in private diagnostics.
Do not catch unrelated programming errors as corrupt data or turn corruption into absence,
INVALID_REQUEST, InvalidStudentDetails, EmailConflict, or an FR-009 rejection.

## Verification

Inventory all business model types and detect missing factory APIs or outside constructor
calls, including imported aliases; allow factories, restoration, internal constructor calls
and intentional misuse/violating fixtures. Verify actual failure contracts and restored
invariants behaviorally. Restore a valid Enrollment after its creation-only eligibility has
changed, and reject corrupt saved IDs/details without adding business conditions. Preserve
StudentEmail Unicode equality/hash and StudentId-based Student equality. Run all mandatory
final checks on the migrated implementation; this contract itself is not execution evidence.
