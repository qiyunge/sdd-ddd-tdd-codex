# Data Model: Student Self-Enrollment

## Domain records

Identifiers are nonempty opaque strings, compared exactly, with no trimming/case folding. This is a technical representation rule, not a new enrollment eligibility condition. Malformed GraphQL types are protocol errors. After successful verification, invalid target StudentId returns INVALID_REQUEST before ownership; invalid CourseId is handled only after ownership passes; no prerequisite queries run. Neither structural check replaces a Domain invariant. Domain constructors and reconstitution enforce nonempty IDs independently of boundary validation.

| Type | Fields / key | Relationships and invariants |
|---|---|---|
| VerifiedIdentity | subject_id | Created only from successful IdentityVerifier output; verification does not imply a Student exists |
| Student | student_id (key), programme_id, name: StudentName, email: StudentEmail | One referenced programme; a dangling programme reference must remain representable so MISSING_PROGRAMME can be returned |
| Programme | programme_id (key) | May offer zero or more courses |
| Course | course_id (key) | May be offered by zero or more programmes |
| ProgrammeCourseOffering | programme_id + course_id (key) | Existing many-to-many relationship; both IDs required |
| Enrollment | student_id + course_id (key) | Immutable association; exactly one pair, no term dimension or synthetic identity required |

Application handles negative identity-verification results before Domain invocation. Domain policy owns self-enrollment ownership for a trusted VerifiedIdentity and target StudentId, duplicate-enrollment rejection and offering eligibility. Application handles absent Student, Programme and Course repository results with the corresponding Core-defined rejection types. It orchestrates exact FR-009 order, loads only data required by the next step and stops at the first rejection. Do not introduce trivial Domain guards for repository None checks or duplicate Domain predicates in Application. Enrollment construction/reconstitution validates structural invariants. A policy/factory creates a new Enrollment only after prerequisite, uniqueness and eligibility checks; reconstitution does not reapply today's eligibility because later offering changes cannot invalidate an existing enrollment.

## Persistence representation

Planned tables: `students(student_id PRIMARY KEY, programme_id NOT NULL, name NOT NULL, email NOT NULL)`, `programmes(programme_id PRIMARY KEY)`, `courses(course_id PRIMARY KEY)`, `programme_course_offerings(programme_id, course_id, PRIMARY KEY(programme_id, course_id))`, `enrollments(student_id, course_id, PRIMARY KEY(student_id, course_id))`. All IDs are NOT NULL TEXT with nonempty checks. Offering and enrollment references can use restrictive foreign keys; no cascading deletes into enrollments. Do not impose a student-to-programme foreign key that prevents the explicitly required dangling-programme scenario. Enrollment must not write prerequisite tables. Fixture/setup tooling owns their creation and population.

The adapter explicitly maps each row to a validated Domain record. Corrupt stored representation maps to a technical failure rather than a valid Domain object or a misleading missing-record rejection. sqlite3.Row, Connection, Cursor and sqlite3 exceptions never escape to Core; the adapter translates them into validated Domain records and Core-owned storage failure types.

## Consistency and transaction lifecycle

1. Application invokes IdentityVerifier and returns Core DENIED immediately on a negative result, without Domain ownership or persistence. On success it supplies trusted VerifiedIdentity and validated StudentId to Domain ownership policy; mismatch returns DENIED before opening persistence.
2. Create a fresh sqlite3 connection with Python 3.12 autocommit=True and issue SQL BEGIN IMMEDIATE before reading prerequisites. Use explicit SQL COMMIT/ROLLBACK, since connection.commit()/rollback() are no-ops in this mode. Create, use and close the connection in one worker thread; no connection sharing, nested BEGIN or implicit transaction defaults. Integration tests prove early lock acquisition and commit visibility.
3. Read Student, its Programme and Course in order. Application immediately returns MissingStudent, MissingProgramme or MissingCourse for an absent result and requests no later data. After all three exist, load the existing enrollment and invoke Domain duplicate policy; only after it passes load offering and invoke Domain eligibility policy. Application sequences and short-circuits these outcomes without duplicating their predicates.
4. If eligible, create the immutable Enrollment, insert, and commit before emitting success. A unique pair constraint provides storage defense. A unique conflict must never cause eligibility to override duplicate precedence; an unexpected conflict triggers rollback and a fresh full ordered evaluation, bounded to one replay, rather than blindly mapping every integrity error to ALREADY_ENROLLED. Other storage errors return PERSISTENCE_FAILURE.
5. On an Application missing-record rejection, Domain policy rejection or technical failure, rollback any active transaction and close the connection. No enrollment cleanup operation or global reset is permitted.

The immediate transaction serializes all local writers. Membership/offering writers using the same database cannot change prerequisites between the decision and commit. A change committed before transaction acquisition is observed; a writer blocked behind enrollment takes effect after that enrollment commits. This establishes the save ordering required by FR-003. No network calls occur inside the write transaction. Independent valid requests can wait behind a rejected request, then proceed normally; lock timeouts are explicit failures, not business rejections.

On pre-commit storage failure the transaction must leave no row. A process or response failure after commit leaves the durable row and a retry follows normal precedence; never compensate/delete a committed enrollment. Ambiguous commit outcomes require reconnect/read diagnostics and an explicit failure response rather than an unverified success; they do not justify deleting a potentially committed row.

## State transitions

`verification failure -> Application DENIED (no ownership call)`; `VerifiedIdentity -> Domain ownership check -> DENIED | prerequisite checks`; `prerequisite checks -> first business rejection | eligible`; `eligible -> pending insert -> committed -> ENROLLED`; `pending insert -> rollback -> PERSISTENCE_FAILURE`. No persisted pending state, enrollment update, withdrawal or delete transition is introduced.

Uniqueness is enforced by both policy and the database. Persisted enrollment remains unchanged on retries, duplicate rejection, later membership/offering changes, or response loss. Unit/integration tests cover construction, reconstitution and every applicable transition.

## Python 3.12 types and explicit bridges

Use distinct frozen dataclass value classes `StudentId`, `ProgrammeId`, `CourseId` and `SubjectId`, with runtime checks for actual string type and nonempty value. Compare exactly, without trimming/case folding or a new UUID restriction. Annotations and NewType alone do not validate runtime values. Frozen fields do not deeply freeze mutable contents; these IDs hold immutable strings. VerifiedIdentity contains SubjectId; Domain explicitly compares its underlying identity to the target StudentId. Verification provenance comes from the trusted port, never a client-provided flag.

Domain records have no Flask, Werkzeug, graphql-core, WSGI, persistence-framework or provider dependency. Student references ProgrammeId rather than a proxy. Missing Programme remains an absent lookup, not an eligibility failure. Tagged result dataclasses/enums represent success, one rejection or technical failure; exhaustive typed converters and tests preserve every outcome.

GraphQL input/context -> neutral Application command, provider result -> Core verification result, sqlite3 columns -> validating Domain constructors, and Core outcome -> GraphQL output are explicit bridges. Adapter-local typed records/dictionaries may represent transport data, but must not cross into Core as graphql-core objects or unchecked Any. Reconstitution exercises the same Domain invariants. Application may use Domain values directly; no duplicate internal DTO layer is needed.

Application sequences repository reads, handles Student/Programme/Course absence itself, and invokes Domain policies through the use case's ordered flow and Protocol ports. Domain does not receive repository-miss checks as trivial guard calls. The resolver adapts a request and delegates; it performs no prerequisite queries, eligibility decisions or transaction orchestration. Output materializes committed identifiers without additional database reads during GraphQL serialization.

In synchronous WSGI execution, the connection lifecycle stays inside the handling worker. On rejection/error issue SQL ROLLBACK only if a transaction is active, then close. On confirmed SQL COMMIT, preserve the durable pair regardless of response or later cleanup failure. If commit outcome cannot be established, report technical failure without compensation and retain normal retry precedence. Threaded tests use separate connections; no check_same_thread=False workaround or global connection.

## Flask transport isolation

Flask introduces no persisted entity or Domain state. Request, Response, current_app, g, session and Werkzeug proxies remain in the HTTP adapter and never become entity fields, Core port types or Domain construction dependencies. Extract neutral input before delegation; keep request/identity data separate from shared app and GraphQL schema state. Flask lifecycle callbacks must not make enrollment decisions or coordinate commits; Application and its UoW retain the transaction lifecycle above.

## Core result ownership

| Result category | Defining layer | Decision owner |
|---|---|---|
| MissingStudent / MissingProgramme / MissingCourse | Application Core contracts | Application handles each corresponding absent repository result |
| Denied (unverified or non-owner) | Core Denied type/value defined in Domain and reused by Application | Application returns it on negative verification; Domain ownership returns it on mismatch after verified input; neither accesses persistence |
| AlreadyEnrolled | Domain policy result | Domain duplicate-enrollment rule |
| CourseNotOffered | Domain policy result | Domain course-offering eligibility |
| Enrollment structural validity | Domain types/factories | Domain construction, reconstitution and transitions |
| Success / technical failure / orchestration result union | Application Core contracts | Application coordinates commit/failure and includes Domain outcomes directly |

Names identify conceptual typed results, not new entities or persisted records. The transport mapper preserves the existing schema reason codes. Domain never imports the Application result union or missing-record types; no redundant wrapper/mapping is required solely between these Core layers. Repository ports return validated Domain records or None. Application must never construct a placeholder Domain object for a missing record or infer failed eligibility from absence.

## Identity verification boundary

IdentityVerifier is an Application-owned Protocol returning VerifiedIdentity or None for a negative verification result. VerifiedIdentity is a trusted Domain value containing validated SubjectId, with no Student record existence implication. Domain ownership accepts VerifiedIdentity and StudentId and owns their self-enrollment identity comparison. Domain has no identity-verification port, verifier invocation, verification-failure decision or UnverifiedIdentity type. None remains an Application port result; it must never reach ownership policy as a fabricated Domain identity.

Application returns the existing Core DENIED on negative verification before constructing target IDs or invoking Domain ownership. After verification succeeds it obtains the target StudentId through its result-returning Domain factory, then invokes ownership; invalid representations remain INVALID_REQUEST without persistence. This clarifies structural-input timing, not FR-009 for well-formed IDs. The existing identity-provider outage technical failure is not a negative identity assertion and also stops before ownership/persistence. CourseId validation follows successful ownership as before.


## Required Student details (extension)

| Value | Stored representation | Domain invariant |
|---|---|---|
| StudentName | name TEXT NOT NULL | Actual string containing a non-whitespace character; original text retained; no uniqueness |
| StudentEmail | email TEXT NOT NULL | Same required-text invariant; whole supplied value casefold() is the comparison key |

Student's frozen fields require both typed values, with no defaults. Construction, reconstitution and validated replacement enforce types and text invariants regardless of caller. The comparison key is derived, not an independent mutable field or client input. No email syntax or length rule is introduced. A Student alone establishes local validity; global email availability additionally requires the Domain uniqueness policy and atomic storage context.

Add typeof/text/nonblank checks to the students table and unique expression index students_email_key on the registered Domain-backed email comparison function, across all students without programme in the key. Register deterministic functions in every persistence connection before schema access; delegate predicates/key conversion to Domain rather than duplicate them in SQL. An unconfigured writer fails closed. Keep original email spelling and do not strip whitespace before indexing. SQL functions must handle invalid/non-text/null values without accidentally making CHECK evaluate to an accepted NULL; explicit NOT NULL/type checks remain required.

Internal student-record operation transitions: raw details -> validated candidate -> locked owner lookup -> Domain email-availability decision -> insert or replacement -> commit -> accepted; invalid details or conflict -> no write/rollback -> typed rejection. For replace, select target by StudentId, use the explicitly supplied programme in the full replacement candidate, and exclude only the same StudentId from conflict. No programme existence rule is added. A missing target or duplicate create ID has its own result. Keep the enrollment UoW unable to write Student. A concurrent claim has exactly one committed winner; a losing replacement retains all previous fields. No save is reported before commit, and success response loss cannot compensate a committed record.

Session.student must select and reconstitute both new fields through Domain values. Invalid persisted text becomes Core StorageFailure and the existing sanitized PERSISTENCE_FAILURE transport result; it is never absence or a new ordered business rejection. Restore only from the compatible constrained schema; legacy/corrupt databases are refused rather than treated as valid global state. No automatic backfill; detect old schema before initialization and leave it untouched. Update all test factories, repository doubles and named-column seed statements to valid unique details. Keep explicit corrupt fixtures for failure testing.

## Validation and failure representation (v2.0.0)

Domain values retain their invariants. Raw-input factories return `ValidValue |
ValidationFailure` and never expose a partially valid Domain value. Guarded internal
constructors may raise on misuse, but Application and adapters must use factories
for expected input validation rather than catch guards as normal control flow.
Student restoration applies the same predicates; invalid stored values are translated
by the persistence boundary to technical StorageFailure, never an input rejection.

Domain policies return rejection/pass values. Repository absence is None. Port writes
return Added/PairConflict for Enrollment or Saved/EmailKeyConflict for Student;
conflicts are values, not exception subclasses. Application coordinates their mapping,
rollback and bounded replay as defined in the boundary contracts. Domain never imports
Application conflict or technical types. Known operational faults may use documented
Core-owned technical exceptions; programming errors propagate to the outer internal
error boundary. No technical exception is silently converted to a business rejection.

## StudentEmail value equality and entity identity

StudentEmail equality compares the complete Unicode `str.casefold()` comparison
key between StudentEmail instances only. Original spelling remains stored but is
excluded from equality/hash. Its immutable hash uses the same key. Return
NotImplemented from `__eq__` for other operand types; never compare directly to a
raw string or another value class. Define equality/hash explicitly so frozen
dataclass defaults do not use original-case text. Unequal keys need not have distinct
hashes; equal values MUST have equal hashes. Hash values are not persistence keys.

Student identity/equality is StudentId alone, independent of email, name and programme.
If Student is hashable, its hash follows StudentId alone. Reconstituted or changed
records retain identity when StudentId is unchanged. Global email uniqueness does
not replace Student identity or merge different StudentIds. The existing email key
used for SQL uniqueness must be identical to the value's equality key.
