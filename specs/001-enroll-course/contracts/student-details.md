# Internal Student Record Integration Contract

**Scope**: Host-only Python integration, not an HTTP/GraphQL management endpoint. This contract adds no GraphQL fields, identity-provider behavior, email login, or enrollment rejection reason. See [data model](../data-model.md) and FR-011–FR-013 in [spec](../spec.md).

## Acceptance boundary and command

The planned Application operation in `enrollment.application.student_details` accepts an explicitly selected CREATE or REPLACE command carrying student_id, programme_id, name and email. IDs retain existing exact nonempty-string semantics. Name/email raw command fields may contain invalid input (typed as object rather than unchecked Any); the operation must validate before producing a Domain candidate. Missing values at the host adaptation boundary are represented as None, never synthesized default details. A replacement supplies the complete desired record. No partial-patch, deletion, list/search, bulk import or management UI is added.

The host is responsible for calling this trusted integration capability; it is not registered as a Flask route or GraphQL resolver. Enrollment callers continue to supply only studentId/courseId. This operation supports existing prerequisite provisioning rather than changing enrollment into student management.

## Results

| Result | Meaning and persistence guarantee |
|---|---|
| Accepted | Valid candidate committed; return StudentId or immutable committed Student, with no lazy reads |
| InvalidStudentDetails(field) | name or email is missing, non-text, empty or whitespace-only; field identifies name/email without echoing sensitive values; no write |
| InvalidIdentifier | Existing ID structural validation failed; no write |
| EmailConflict | A different StudentId owns the whole-address casefold key, irrespective of programme; no creation or change |
| StudentAlreadyExists | CREATE targets an existing StudentId; no replacement and no accidental email-conflict classification |
| StudentNotFound | REPLACE targets an absent StudentId; no creation |
| StudentStorageFailure | Lock/open/read/write/commit failure, incompatible schema or corrupt stored record; no raw SQL/exception detail |

Domain defines invalid-text and email-conflict outcomes; Application defines operation existence/technical results (StudentStorageFailure for the returned technical outcome) and composes them without Domain importing Application. Match existing Core typed-result conventions. Invalid text is distinguishable from email conflict. Name is validated before email when both are invalid; this deterministic internal choice does not alter FR-009.

## Processing and ports

1. Validate command IDs and required text with Domain result-returning factories; branch on failures without catching constructor exceptions. Pass validated StudentId, ProgrammeId, StudentName and StudentEmail to Student.create; Entity factories do not parse raw values. Missing/null values cannot become valid Domain values.
2. Open a separate Application-owned student-record transaction via a factory, registering required adapter SQL functions and taking BEGIN IMMEDIATE before reads. Do not extend the enrollment UoW with Student writes.
3. Load target by StudentId to select existing-create or absent-replace results. If applicable, stop without writing. No programme lookup is required or implied.
4. Load the owner of the candidate email comparison key across the entire students table. Return StudentId or None through the port; never expose a sqlite3 row/connection. Domain policy compares owner with candidate StudentId and permits absent/self ownership, otherwise returns EmailConflict. Application branches on the policy outcome without repeating its predicate.
5. Insert or replace that Student's fields with bound SQL and no REPLACE/IGNORE conflict suppression. Preserve enrollment rows and other students. The unique expression index remains the final concurrency guard; return EmailKeyConflict only for its precise unique violation; Application translates that port outcome to Domain EmailConflict. All other integrity failures retain their own classification.
6. Explicitly COMMIT before Accepted. On rejection or pre-commit error ROLLBACK and close. A confirmed commit is not undone by response loss. An ambiguous commit reports technical failure without destructive compensation.

The separate student-record UoW offers target read, email-owner read, insert, replace, commit, rollback and close. Application owns these Protocols; persistence implements them. Domain has no repository port for this rule because Application supplies the contextual owner to a pure policy. A constructor cannot establish global uniqueness without this context.

## Stored representation and compatibility

Persist original name/email as required TEXT, checking nonblank with a Domain-backed registered function. Index the whole-address Domain casefold function uniquely with no programme component. Register deterministic functions on initialization and every connection, including host/fixture write connections; an unconfigured connection must fail closed. Test direct SQL attempts against the configured production schema, not only the Application preflight. The host must use the provided connection setup for direct provisioning and cannot invent an independent normalized key.

Legacy schemas without required fields are unsupported and must be detected without destructive changes. The host supplies valid replacement data and handles migration externally. Fresh initialization and compatible repeated initialization must work; neither inserts default names/emails. Runtime encountering invalid Student rows uses the separate controlled Domain reconstitution API and translates InvalidPersistedState to Core DataIntegrityFailure(StorageFailure), never a missing-student, user-input or eligibility result.

## Acceptance identities

New `tests/acceptance/test_student_details.py` must define stable scenario IDs `student-details-1` through `student-details-7` corresponding to User Story 2; parameter variants retain their parent identity. Exercise real file-backed SQLite, reopen to verify persisted outcomes, and use separate worker-owned connections for races. Test restoration through the repository as well as creation/change. Preserve all existing enrollment acceptance identities. Manifest validation must require both complete sets, not just total test counts.

Supplement with Unicode case expansion, non-ASCII whitespace, non-string values, unchanged spelling, significant surrounding whitespace, direct-constraint enforcement, function registration failure, invalid-row conversion, old-schema refusal, compatible initialization, and unrelated constraint failures. No latency or throughput promise is added.

## Failure propagation and internal contracts

InvalidIdentifier, InvalidStudentDetails, EmailConflict, StudentAlreadyExists and
StudentNotFound are returned values, never raised exceptions. Domain Value Object factory
signatures are conceptually `create(raw: object) -> Value | ValidationFailure`;
record factories accept valid component values and return valid records or explicit
record validation outcomes. Name-before-email validation remains deterministic.
Guarded direct construction rejects internal misuse but is never the normal parser
for untrusted input. Reconstitution is a separate controlled API using persisted-state invariants, without
creation-only eligibility; InvalidPersistedState becomes DataIntegrityFailure(StorageFailure),
not an InvalidStudentDetails business rejection to the host.

Student-record port insert/replace return `Saved | EmailKeyConflict`. Reads return
validated records or None; commit/rollback/close return None on successful completion.
Factory/open, reads, writes and transaction operations may raise only the documented
Core-owned StorageFailure for recognized storage/compatibility faults. Application
translates that technical exception into the distinct StudentStorageFailure result. Neither
kind of technical failure is an email conflict. Infrastructure exception types stay
inside the adapter; precise driver constraint catches implement the port outcome.
Unexpected programming/internal-contract exceptions propagate to the host error
boundary, which records diagnostics and reports a sanitized internal failure; it
MUST NOT convert them to invalid details, conflict or missing student. Cleanup must
preserve the primary failure and confirmed commits.

## Value equality and Student identity

Returned StudentEmail values compare equal only to StudentEmail instances with the
same complete Unicode `str.casefold()` key. Equal values have equal hashes, including
casefold expansions such as `Straße@example.com` and `STRASSE@EXAMPLE.COM`.
Original submitted text remains available unchanged. For unrelated operands,
`__eq__` returns NotImplemented; no string coercion or cross-value-class equality.
Set membership and dictionary lookup must agree with this equality. Hashes are
process-local, not database keys or externally stable identifiers.

Student identity/equality uses StudentId alone. A name/email/programme replacement
keeps the Student's identity, including a case-only email replacement. Equal email
values do not make different StudentIds the same entity. The conflict policy excludes
self by StudentId; separate student records remain subject to global email uniqueness.

## Construction and integrity alignment

Apply the [Domain construction contract](domain-construction.md) and shared
[D2/D3](../../../.specify/memory/architecture-decisions.md). Normal creation uses factories
with validated Entity component types; persisted rows use explicit controlled reconstitution
called directly by Persistence Adapters. Internal constructors are not public alternatives.
Data-integrity failure remains internally distinguishable from availability faults, while
existing sanitized public technical outcomes are preserved. This alignment changes no
GraphQL fields/reasons, public request shape, email rules or FR-009 order. Behavioral tests
and explicit semantic review complement structural dependency checks; imports alone do not
prove correct conversion or failure classification.
