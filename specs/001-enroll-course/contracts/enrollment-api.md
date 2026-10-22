# GraphQL Enrollment and Core Port Contracts

## Public acceptance boundary

Flask serves GraphQL over HTTP POST `/graphql`, with one SDL-first business mutation defined in [schema.graphqls](schema.graphqls). The minimal Query `_empty` field is required schema scaffolding, returns null and performs no I/O; it adds no business query. No subscriptions, batches as an extra API, federation, new read/management operations or UI are introduced.

Each request carries JSON `query`, optional `operationName` and `variables`. A mutation input contains target `studentId` and `courseId`. Opaque credentials arrive in the Authorization header/context, not in GraphQL input, and are not logged. Transport reads the header into a neutral Application-owned credential representation. Application calls IdentityVerifier; a matching asserted studentId alone never establishes verification. Production supplies an external verifier bridge; tests inject deterministic outcomes. No new identity-provider implementation or account API is included.

Example GraphQL document:

```graphql
mutation Enroll($input: EnrollCourseInput!) {
  enrollCourse(input: $input) {
    __typename
    ... on EnrollCourseSuccess { studentId courseId }
    ... on EnrollCourseRejected { reason }
    ... on EnrollCourseFailure { failureReason: reason }
  }
}
```

Variables: `{"input":{"studentId":"student-1","courseId":"course-1"}}`. GraphQL ID values are opaque strings; standard GraphQL integer-to-string ID coercion may occur at the transport boundary. Explicit conversion preserves the coerced value exactly; no implicit UUID restriction or case folding. Clients should send string IDs. Null/missing required inputs and incompatible GraphQL types fail schema validation before resolver execution, with no persistence access.

## Result union and observable outcomes

| Core outcome | GraphQL type / reason | Payload rule |
|---|---|---|
| ENROLLED | EnrollCourseSuccess | Committed studentId/courseId only; success is not returned before commit |
| Unverified or non-owner | EnrollCourseRejected / DENIED | Identical generic result for both cases, no target record/eligibility/enrollment detail |
| Missing student | EnrollCourseRejected / MISSING_STUDENT | One distinguishable reason |
| Missing programme | EnrollCourseRejected / MISSING_PROGRAMME | One distinguishable reason |
| Missing course | EnrollCourseRejected / MISSING_COURSE | One distinguishable reason |
| Existing pair | EnrollCourseRejected / ALREADY_ENROLLED | Existing row unchanged; do not check offering |
| Ineligible course | EnrollCourseRejected / COURSE_NOT_OFFERED | No enrollment mutation |
| Persistence failure | EnrollCourseFailure / PERSISTENCE_FAILURE | Generic technical reason, no SQL or exception details |
| Identity dependency unavailable | EnrollCourseFailure / IDENTITY_UNAVAILABLE | No record detail and no persistence access; not proof that identity is unverified |
| Invalid target StudentId after verification, or CourseId after ownership | EnrollCourseFailure / INVALID_REQUEST | No prerequisite data; supported Domain factories still enforce invariants |

Enum values are the stable machine-readable reasons; presentation text can map them to clear messages. Returning a rejection never returns a success object or multiple rejection reasons. Union resolution and output conversion are explicit adapter responsibilities. Expected business outcomes use the data union with no GraphQL errors. Well-formed execution returns HTTP 200 for these outcomes; HTTP status alone is never proof of enrollment success. Malformed HTTP/GraphQL requests are protocol failures; tests assert error responses, no data disclosure and zero mutations rather than reinterpret them as missing-record business reasons. Unexpected resolver/serialization errors must be sanitized and must not undo a committed enrollment.

## Ordered business processing

For a structurally executable mutation:

1. Application calls its Application-owned IdentityVerifier port. If the result is None (verification does not establish a trusted identity), Application immediately returns Core DENIED. Do not invoke Domain ownership, construct an UnverifiedIdentity, open a UoW or access persistence.
2. On successful verification, Application constructs the validated target StudentId and passes it with trusted VerifiedIdentity to Domain ownership policy. Domain compares the subject identifier with the student identity exactly, without trimming or case folding, and returns the same Core DENIED on mismatch. Domain never calls IdentityVerifier or any identity-verification port. No database session or lookup is allowed for either denial. An unusable target student identity—missing, empty, or not text—is INVALID_REQUEST after verification and before ownership (FR-014). It is not a generic denial, not a missing student, and not an FR-009 reason. Well-formed IDs follow exact FR-009 ordering.
3. After ownership passes, convert the remaining raw CourseId through validating Domain mechanisms. An unusable course identity is INVALID_REQUEST before the missing-course check (FR-014), not a missing-record or offering inference.
4. Open an atomic session and load Student. Application handles an absent result by returning the Core-defined MissingStudent rejection (MISSING_STUDENT); do not call a Domain existence guard or request Programme.
5. Load that student's Programme. Application handles absence by returning Core-defined MissingProgramme (MISSING_PROGRAMME); do not call a Domain existence guard or request Course.
6. Load Course. Application handles absence by returning Core-defined MissingCourse (MISSING_COURSE); do not call a Domain existence guard or request enrollment/offerings.
7. Load enrollment for the pair, invoke Domain duplicate-enrollment policy and stop on existing enrollment. Offering is not loaded/evaluated here.
8. Load current offering under the same immediate transaction, invoke Domain offering-eligibility policy, create Enrollment through Domain, add and commit.
9. Return success only after confirmed commit; materialize response without additional persistence reads.

This preserves FR-009's exact order: unverified -> mismatch -> missing student -> missing programme -> missing course -> already enrolled -> course not offered. No eager fetching or error accumulation. A missing prerequisite prevents dependent checks. Identity verification may succeed without a Student record. Structural GraphQL errors occur before resolver execution and disclose no record state; they are not enrollment business rejection ordering.

Concurrent HTTP requests have independent transaction sessions; GraphQL's serial top-level mutation execution within one operation supplies no cross-request protection. Each mutation invocation commits independently. Response loss after confirmed commit leaves the pair intact; a retry reevaluates normal precedence and never compensates/deletes the earlier row. Multiple top-level mutation invocations, if present in one standard GraphQL document, do not imply all-or-nothing operation-level transactions.

## Core-owned Python contracts and bridges

Application exposes a plain Python enrollment use case receiving a neutral command with raw target IDs and opaque credentials and returning a closed Core-owned outcome. Commands can contain incomplete input; they must not label it as valid Domain state. No Flask/Werkzeug request, Response or context proxy, graphql-core context or GraphQLResolveInfo, WSGI environ, HTTP object, sqlite3 type or SDK type appears in Core signatures. Application-owned Protocols describe ports; annotations are enforced by static checks, while supported Domain factories/reconstitution enforce runtime invariants.

- **IdentityVerifier**: is Application-owned, verifies neutral credentials and returns trusted Domain VerifiedIdentity or None for negative verification; provider failure translates into a Core-owned technical failure. Verification does not query or infer Student existence. The trusted adapter implements verification; caller-supplied `verified=true` is not supported.
- **EnrollmentUnitOfWorkFactory**: opens one atomic session after identity and ownership checks. The immediate write lock precedes all prerequisite reads. Application owns commit coordination; adapter owns sqlite3 mechanics.
- **Session reads**: Student by StudentId -> Student or absent; Programme by ProgrammeId -> Programme or absent; Course by CourseId -> Course or absent; Enrollment by pair -> Enrollment or absent; offering by pair -> ProgrammeCourseOffering or absent. Domain values or None represent presence/absence; sqlite3 rows do not cross the port. Application immediately handles Student/Programme/Course absence, then invokes Domain duplicate and offering policies when reached. It requests later data only after the preceding step passes.
- **Session writes**: add validated Enrollment, commit, rollback/close. No prerequisite mutation methods. SQL parameters are bound; no string-concatenated identifiers from request data. One connection per invocation, closed after success/rejection/failure.
- **Port failures**: row corruption and sqlite3 errors become Core-owned storage failures, never sqlite3 exceptions or a fake missing-record result. A detected pair uniqueness conflict permits at most one fresh full ordered evaluation after rollback, preserving higher-priority reasons. Other integrity failures must not be labeled ALREADY_ENROLLED. The immediate-transaction design should normally let the second valid request observe the first pair before insert.

Explicit bridges are GraphQL DTO/context -> Application command; provider result -> Core verification; sqlite3 columns -> controlled Domain value/record reconstitution; Core outcome -> GraphQL DTO. Domain invariants apply during construction and reconstitution. Direct adapter use of public Domain mechanisms is permitted. No extra mapping layer is required between Application and Domain when their representation is already the same.

## Verification obligations

Execute the SDL with real documents/variables to test coercion, non-null fields, result union resolution, unknown fields and all outcomes. HTTP acceptance tests verify headers/context and endpoint wiring, using pytest, Flask's test client, an injected identity double and real file-backed SQLite. A local Waitress socket smoke/concurrency test also verifies the server route and worker behavior. Focused converter tests cover invalid stored values and absence of external types/exceptions. A persistence spy fails any access on DENIED. Domain tests cover construction/reconstitution/transitions; Application port spies prove ordered short circuits. Integration tests cover commit ordering, real rollback, concurrency and changes to eligibility. Import Linter and architecture/signature tests check the dependency graph and public types; behavioral tests prove conversion semantics it cannot infer.

## Python runtime and verification configuration

The GraphQL adapter loads SDL with graphql-core build_schema and explicitly binds a synchronous mutation resolver, union type resolver and output field/enum conversions. A Flask application mounts only `/graphql` and reads credentials into a neutral command; Application calls the verification port. Waitress serves the application in worker threads. Flask's test client covers in-process HTTP/JSON/header/schema behavior; actual server tests separately prove routing and concurrent worker handling. Core code never receives WSGI environ or resolver info.

A plain Python use-case signature accepts a neutral enrollment command and returns a tagged Core result. Domain IDs are distinct validated classes, not aliases or unchecked strings labeled valid. Protocol methods have complete annotations. Scope strict mypy checks across source, including conversions; isolate unavoidable library typing gaps at adapters with explicit validation and justification.

The UoW adapter opens sqlite3 with autocommit=True, executes BEGIN IMMEDIATE before prerequisite reads, executes explicit SQL COMMIT/ROLLBACK, and closes in the same worker. Connection commit()/rollback() must not substitute for SQL in this mode. No global connection, ORM, ASGI dependency or asynchronous transaction splitting is introduced.

Complete Core source coverage is measured with coverage.py branch=True and fail_under=100, including unimported modules and full affected functions/methods. Import/signature fitness checks and runtime converter tests complement strict typing. No business branch exclusions or changed-lines approximation. Lightweight behavioral Red/Green execution evidence for cohesive increments, refactoring consideration with relevant tests passing, and final-state checks are required; passing type checks or coverage alone does not establish TDD or correctness.

## Direct graphql-core adapter contract

Use build_schema with the checked-in SDL and schema validity checks during initialization. Explicitly attach Mutation.enrollCourse.resolve and EnrollCourseResult.resolve_type; return the SDL object type name from union resolution, not a GraphQLObjectType or a Domain class. Query._empty returns None without I/O. Build and wire once; per-request credential/context values are separate and never mutate the shared schema.

The synchronous resolver accepts the engine's source/info/input arguments, maps input IDs and info.context credentials to a neutral Application command, invokes Application once and converts the outcome to an adapter-owned output mapping. Mapping keys match SDL camelCase exactly and reason values match SDL enum names. A trusted adapter tag selects EnrollCourseSuccess, EnrollCourseRejected or EnrollCourseFailure; client input must not choose the outcome type. Do not rely on automatic Domain attribute or enum mapping.

Invoke graphql_sync with explicit context_value, variable_values, operation_name and check_sync=True. GraphQLResolveInfo, GraphQLSchema, GraphQLError and ExecutionResult are transport engine types and cannot enter Core contracts. Error formatting distinguishes safe parse/validation feedback from unexpected internal exceptions; remove raw original_error, stack traces, credentials, SQL and provider details. Preserve GraphQL data/errors envelope semantics, including null propagation; never replace a failed execution with a fabricated success.

The Flask HTTP adapter routes only `/graphql`: unknown path -> 404; unsupported method -> 405 with Allow: POST; non-JSON media type -> 415; malformed JSON or envelope shape -> 400. POST application/json accepts one object with query string, optional operationName string/null and variables object/null. Do not accept a client-asserted acting identity or verification flag. Well-formed requests receive application/json GraphQL result responses; expected union outcomes use HTTP 200. Syntax/validation/execution error-envelope handling is adapter-tested and must not disclose record state or call persistence for a non-executable document. No HTTP batching, GET mutations or additional protocol surface is needed.

The Flask HTTP adapter can call the GraphQL execution adapter as one composed inbound pipeline. This is a declared technical dependency; no persistence or identity adapter is imported by either. Bootstrap supplies the Application use case through injection. Automated tests verify HTTP, binding and formatting responsibilities and may span layers through a shared boundary. Cohesive increments retain lightweight Red/Green evidence and consider refactoring with relevant tests passing; separate cycles per assertion or branch are not required.

## Flask HTTP Transport Adapter

Create a Flask application through an adapter app factory supplied with the GraphQL executor and explicit configuration from bootstrap. Register a synchronous POST /graphql route; the view adapts the request and invokes the executor. It must not access prerequisite records, decide eligibility, implement identity verification or coordinate transactions. graphql-core wiring and Application orchestration retain their existing ownership.

Read JSON through Flask request APIs with normal media-type/error behavior, then validate the existing envelope fields. Convert headers into neutral credentials before building the adapter-owned graphql-core context. Never pass flask.request, g, current_app, session, Response, Werkzeug Request or LocalProxy into Core or the GraphQL resolver; no request-scoped identity is stored on the shared app/schema. Core must remain callable without a Flask application/request context.

Disable the unused static route and automatic OPTIONS on /graphql to preserve the specified POST-only surface. Flask HTTP error handlers return JSON while preserving original HTTP status and headers (especially Allow on 405). Wrong media types remain 415, malformed JSON/envelopes remain 400, and unknown paths remain 404. Expected business outcomes still use the existing union and HTTP 200. Test unexpected failures with production-like exception handling as well as testing mode; default test exception propagation must not bypass verification of sanitized responses.

Application/UoW still commits explicitly before success and rolls back its own active transaction on failure. Flask teardown is not an enrollment transaction coordinator and must not undo a committed enrollment. A worker owns its sqlite3 connection lifecycle; no Flask proxy or connection is shared across concurrent workers. Keep debug disabled for real server/error-response checks. Waitress hosts the resulting Flask WSGI application; Flask's development server is not the deployment target.

## Application existence handling and Domain policy ownership

Application owns the complete first-match sequence; Domain owns self-enrollment authorization, duplicate and offering decisions and Enrollment invariants. Application immediately returns Core DENIED on negative IdentityVerifier output without invoking ownership or persistence. Only after successful verification does it pass trusted VerifiedIdentity and StudentId to Domain ownership policy, which returns the same DENIED on mismatch. Domain knows neither the verifier port nor an UnverifiedIdentity model. After authorization, Application distinguishes repository None results for Student, Programme and Course and returns Application-Core-defined missing-record types directly. Those types preserve the existing GraphQL reasons; they are not transport errors or Domain invariant exceptions.

Do not add Domain require-exists/None-guard functions or entity placeholders. Domain policy inputs are validated records/value objects and relevant enrollment/offering facts when reached. The duplicate rule determines whether an existing pair forbids enrollment; the offering rule determines eligibility. Application must not implement or repeat actor comparison, duplicate rejection or offering-membership predicates. Branching to propagate a Domain rejection is legitimate orchestration. Do not fetch offering facts or invoke eligibility after the duplicate policy rejects.

Application's result union uses its own missing-record/success/technical outcomes and Domain policy outcomes directly. Domain does not depend on Application; adapters convert each Core result into the unchanged GraphQL union. Persistence adapters return records/None or Core technical failure, never select use-case rejection order. Tests verify the ownership split through public outcomes and meaningful short circuits rather than enforcing trivial guard APIs or a mirrored test file per class.

## Verification failure and ownership call boundary

The Application port contract is `verify(neutral_credentials) -> VerifiedIdentity | None`, with existing Core technical failure for identity-provider unavailability. None means verification failed and Application returns DENIED directly; it is not a Domain model or a reason to query Student. A technical provider failure also stops before ownership/persistence under the existing IDENTITY_UNAVAILABLE contract. Domain ownership takes only trusted VerifiedIdentity and target StudentId; no verification result wrapper, None, credentials, SDK type or verification port is passed to it.

Core Denied is reusable from Domain by Application, so both negative verification and ownership mismatch map identically to EnrollCourseRejected/DENIED without a new outward reason or duplicated internal result mapping. Application does not compare subject/target identities itself. The exact sequence for executable, structurally valid enrollment requests remains Application verification -> Domain ownership -> Application missing Student -> missing Programme -> missing Course -> Domain duplicate policy -> Domain offering eligibility. Stop immediately at each rejection.


## Student detail extension compatibility

Student reads now return records containing required Domain-validated name and email. Enrollment input/output SDL and FR-009 sequencing remain unchanged: no new detail arguments or email-conflict rejection is added here. Enrollment never creates/edits Student records. Corrupt persisted details are DataIntegrityFailure(StorageFailure), while incompatible schema faults retain technical storage classification; both map to the existing sanitized PERSISTENCE_FAILURE, rather than MISSING_STUDENT or a new eligibility rule. Host-only record establishment and replacement use the separate [student-details contract](student-details.md); its outcomes are not GraphQL enum additions.

## Expected outcomes and unexpected failures (current feature alignment)

The existing SDL is unchanged. DENIED, missing-record, ALREADY_ENROLLED,
COURSE_NOT_OFFERED and structural INVALID_REQUEST are expected returned outcomes.
INVALID_REQUEST retains its existing EnrollCourseFailure representation; that SDL
type name does not classify it as an unexpected technical failure. Domain parsing
factories return valid IDs or explicit validation failures. Application branches on
those values at the established verification/ownership timing; it MUST NOT catch
constructor ValueError/TypeError to implement normal input rejection.

Enrollment UnitOfWork.add returns `Added | PairConflict`. Reads return valid records
or None, and commit/rollback/close return None on success. PairConflict is a returned
Core-owned value and replaces the raised UniqueConflict contract. Application rolls
back/closes and retries the complete ordered attempt once. A second conflict becomes
a Core technical StorageFailure mapped to PERSISTENCE_FAILURE, without inventing a
business conclusion. Only the precise enrollment-pair constraint maps to PairConflict.

IdentityVerifier returns VerifiedIdentity or None for ordinary verification. Known
provider operational exceptions translate to Core IdentityUnavailable; known operational storage faults translate to Core StorageFailure; invalid persisted state translates to its DataIntegrityFailure subtype as specified in [plan.md](../plan.md). These documented
technical exceptions may be raised by ports, then translated by Application to
IDENTITY_UNAVAILABLE or PERSISTENCE_FAILURE. They never become business rejection,
negative verification, repository absence or INVALID_REQUEST. No sqlite3/provider
exception type crosses into Core.

Unexpected programming or internal-contract exceptions propagate out of Application
and are sanitized by the outer GraphQL/HTTP error boundary as internal execution
errors, with diagnostics retained outside public responses. Do not catch Exception
in the verifier/use case to fabricate DENIED, business rejection, or a provider outage.
GraphQL errors retain null propagation and cannot imply rollback after confirmed
commit. The host-only Student operation follows its separate failure contract.

## Construction and integrity alignment

Apply the [Domain construction contract](domain-construction.md) and
[plan.md](../plan.md). Normal creation uses factories
with validated Entity component types; persisted rows use explicit controlled reconstitution
called directly by Persistence Adapters. Internal constructors are not public alternatives.
Data-integrity failure remains internally distinguishable from availability faults, while
existing sanitized public technical outcomes are preserved. This alignment changes no
GraphQL fields/reasons, public request shape, email rules or FR-009 order. Behavioral tests
and explicit semantic review complement structural dependency checks; imports alone do not
prove correct conversion or failure classification.
