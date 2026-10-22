# Implementation Plan: Student Self-Enrollment

**Branch**: `001-enroll-course` | **Date**: 2026-10-21 | **Spec**: [spec.md](spec.md)

**Baseline**: Constitution v2.0.0 and the approved feature specification.

**Input**: `specs/001-enroll-course/spec.md`; Project Owner requires Python as the development
language, graphql-core as the GraphQL engine, and Flask as the HTTP Transport Adapter.
Application owns repository absence handling and exact FR-009 sequencing; Domain owns business
policies and invariants.

## Summary

Implement with Python 3.12, graphql-core SDL-first GraphQL, Flask as the synchronous HTTP
Transport Adapter, Waitress WSGI serving and embedded sqlite3 persistence. Framework-free Domain
owns self-enrollment authorization, duplicate-enrollment and offering-eligibility policies and
Enrollment invariants; Application handles failed identity verification and repository misses
and orchestrates FR-009 through owned ports; adapters perform explicit boundary conversions. The
owner selects Python, graphql-core and Flask directly. Preserve FR-001–FR-010 and all fifteen
enrollment acceptance scenarios; extend Student for FR-011–FR-013, User Story 2 scenarios 1–7,
and SC-005–SC-007 alongside SC-001–SC-004 and Constitution v2.0.0.

## Technical Context

**Language/Version**: Python 3.12; declare >=3.12,<3.13 for the initial supported/tested
runtime. No Java build/runtime dependency.

**Primary Dependencies**: graphql-core (>=3.3,<3.4; import package `graphql`) with Flask
(>=3.1,<3.2) and Waitress at runtime plus Python standard library (`sqlite3`, `dataclasses`,
`typing`). Development: pytest, HTTPX for real socket tests, coverage.py, mypy, Ruff and Import
Linter. Retain existing pyproject.toml and committed uv.lock for this extension; no dependency
upgrade is required.

**Storage**: Local file-backed SQLite, five persisted record types, one immediate
transaction/connection per enrollment. No ORM or database server.

**Testing**: pytest; Flask's test client exercises HTTP POST `/graphql` with real GraphQL
documents, JSON and credential headers. Acceptance uses real SQLite and an injected
deterministic verifier. Add real local Waitress socket smoke/concurrency tests. Focused
Domain/Application, adapter, schema and architecture tests complement acceptance.

**Target Platform**: Python 3.12 on Linux, one threaded WSGI process and local database. Each
request creates/uses/closes its connection in the same worker; no global connection or async
offload needed.

**Project Type**: One Python package with GraphQL HTTP enrollment and an internal host
student-record integration operation.

**Performance Goals**: No latency, throughput or volume targets specified. SQLite serializes
writers; no distributed deployment or performance guarantee is introduced.

**Constraints**: Exact FR-009 precedence, generic identity denial before persistence, save-time
eligibility, pair uniqueness, commit before success, no mutation caused by rejection.
Five-second bounded lock wait maps to technical failure. Production identity verification and
prerequisite-management interfaces remain externally supplied; internal student-record
integration enforces the new invariants.

**Scale/Scope**: Five persisted record types, one GraphQL mutation, and an internal
student-record integration operation; query-root placeholder is schema scaffolding. No UI,
management operations, capacity, terms, fees, withdrawal, federation, subscriptions, broker,
containers or extra services.

## Constitution Check

*GATE: assessed before Phase 0; re-evaluated after Phase 1. PASS means design conformity with
implementation obligations, not executed application checks.*

| Principle | Before research | Post-design obligation |
|---|---|---|
| I. Inward dependencies | PASS: Python supports owned ports and adapters | PASS: Import Linter and architecture/signature tests enforce inward dependencies, Core independence and no framework/persistence leakage |
| II. Domain integrity / Full Bridge | PASS: Domain retains policies; Application handles repository misses | PASS: explicit expected-failure results, Domain-owned validating factories, separate technical exception contracts, Application first-match sequencing and invariant-safe construction/reconstitution; explicit GraphQL/provider/row/outcome conversion; no redundant Application–Domain mappings |
| III. Outside-In TDD | PASS: both acceptance boundaries declared | PASS: HTTP enrollment and Python student integration guide cohesive Red/Green/Refactor increments; shared layer tests and consolidated lightweight evidence are permitted |
| IV. Fitness / coverage | PASS: enforcement strategy selected | PASS: whole-affected-business-function 100% branch minimum; approved complete-Core 100% statement-and-branch target retained; focused architecture fixtures |
| V. Evidence / quality | PASS: final-state review required | PASS: pytest, coverage, mypy, Ruff, Import Linter, architecture and evidence checks must run and pass on final implementation state |

No deviations or constitutional exceptions. No implementation checks are claimed to have passed
during planning.

### Resolved constitutional planning questions

- **Boundary contracts**: Keep [SDL](contracts/schema.graphqls) and
  [contract](contracts/enrollment-api.md). Flask/Werkzeug request/response/context proxies,
  graphql-core execution context/types, WSGI environ, HTTPX objects, sqlite3
  rows/connections/exceptions and identity SDK types stay outside Core. Commands can contain raw
  invalid input; Domain factories return explicit validation outcomes before guarded
  construction of valid state. Adapters may directly call public Domain constructors for
  technical adaptation without orchestrating the use case. Application may directly use Domain
  values; no redundant mapping solely for layering.
- **Port ownership / context**: One Enrollment context. Application owns IdentityVerifier and
  EnrollmentUnitOfWork/Factory Protocols because orchestration needs them. Domain needs no
  external capability port. No cross-context messaging or distributed transactions.
- **Transaction coordination**: Application invokes its IdentityVerifier port. A failed
  verification returns the Core-defined DENIED immediately, without a Domain ownership call or
  persistence. On success it passes the trusted VerifiedIdentity and validated target StudentId
  to Domain ownership policy; mismatch returns DENIED before persistence. It loads Student,
  Programme and Course sequentially, handles each absent repository result by immediately
  returning its Core-defined missing-record rejection, and calls Domain duplicate and
  offering-eligibility policies only when their prerequisite records exist. It creates
  Enrollment through Domain, adds and commits through the port, then returns success. No trivial
  Domain existence guards or duplicate Application business predicates are introduced. The
  sqlite3 adapter implements explicit SQL BEGIN IMMEDIATE/COMMIT/ROLLBACK with autocommit=True
  and closes its worker-owned connection. No SQL or business predicates in the GraphQL resolver.
- **Rejection ownership and ordering**: Application owns FR-009 sequencing: unverified identity
  -> non-owner -> missing Student -> missing Programme -> missing Course -> already enrolled ->
  course not offered. Application handles unverified identity at stage 1; Domain ownership
  decides mismatch at stage 2 only after verification succeeds. Neither denial accesses
  persistence. Application handles repository absence for the next three; Domain decides
  duplicate and offering eligibility when reached. Application may branch on typed Domain
  outcomes to short-circuit but must not recalculate their predicates. Missing-record rejection
  types live in Application Core contracts; Domain policy reasons remain in Domain and are used
  directly in the Application result union. Domain never imports Application result types.
- **Verification boundary**: IdentityVerifier is Application-owned; its ordinary result is
  trusted Domain VerifiedIdentity or None when credentials do not establish a verified identity.
  Application returns the same Core DENIED on None without invoking ownership or opening a UoW.
  Domain ownership accepts only VerifiedIdentity and StudentId; it neither calls
  IdentityVerifier nor depends on any verification port or UnverifiedIdentity model. The Core
  Denied value/type can remain Domain-defined and be reused by Application, preserving inward
  dependencies and the identical public denial. Existing provider-unavailability technical
  failures remain distinct from a negative verification result and also short-circuit before
  Domain/persistence.
- **GraphQL/HTTP ownership**: graphql-core is the schema/execution engine, not an HTTP
  application/server. Flask owns HTTP routing, request parsing and response construction. Its
  adapter owns method/content/envelope checks, credentials/context, execution invocation and
  sanitized JSON responses; Waitress owns sockets/workers. Bootstrap injects the GraphQL
  executor and Application dependencies into a Flask app factory; no Flask context is passed
  inward. GraphQL wiring owns SDL binding, explicit union type names and output conversions.
  Build schema/wiring once, then avoid per-request schema mutation. Engine objects stay inside
  inbound adapters. Tests verify these technical responsibilities and may share a behavioral
  boundary across layers.
- **Flask lifecycle**: An app factory configures dependencies and routes once. The synchronous
  POST /graphql view extracts JSON and credentials, invokes the injected GraphQL adapter and
  formats JSON responses. Keep Flask request/current_app/g/session proxies and Werkzeug types
  out of Domain, Application and GraphQL resolver contracts. Use an adapter-owned plain
  execution context. Preserve the POST-only protocol by disabling automatic OPTIONS for this
  route and the unused static route. HTTP error handlers preserve status/Allow headers and
  return sanitized JSON; do not turn unexpected errors into success.
- **Application frameworks**: Choose no framework dependencies in Core for this feature. This
  does not amend the constitution's general permission for appropriate Application frameworks.
  Dataclasses, enums and typing are standard-library mechanisms;
  Flask/graphql-core/Waitress/HTTP and database modules remain adapters/bootstrap.
- **Fitness scope**: Preserve inward dependencies, Domain isolation, public boundary type
  isolation and semantic conversion checks. Import Linter is the primary static dependency
  verifier; focused supplemental checks cover its gaps. See “Architecture fitness
  simplification” for consolidation and verification criteria.
- **TDD scope**: Acceptance-guided Outside-In TDD uses cohesive behavioral increments. Execute
  relevant tests that fail for the expected behavioral reason before implementation; implement
  the increment's required behavior and verify relevant tests pass; consider refactoring and
  verify relevant tests remain passing. Related behaviors MAY form one coherent implementation
  unit. Separate cycles per assertion, branch, or independently testable behavior are not
  required. Automated tests verify every affected layer and MAY exercise several layers through
  one shared behavioral boundary. Configuration/documentation validation does not require
  artificial Red; pure refactors start green. Refactoring need not change code.
  Import/configuration failures alone are not behavioral Red; do not weaken tests to obtain a
  pass.
- **Approval**: Project Owner remains specification/change and future exclusion approval
  authority. The existing ready-for-planning spec is the baseline. Python selection is
  explicitly authorized; the updated spec authorizes the Student detail extension; this plan is
  aligned with the current Constitution v2.0.0; no new ratification claim is made.
- **Evidence**: Retain lightweight commands/results demonstrating relevant behavioral Red before
  implementation and Green afterward. Consolidation across cohesive increments is permitted.
  Review actual execution evidence; passing tests or coverage alone do not prove TDD. See
  “Execution evidence and tooling migration” for the replacement design, historical reassessment
  and final-result integrity requirements.
- **Coverage scope**: Retain the approved complete-Core 100% statement-and-branch gate,
  including unimported modules and business behavior introduced elsewhere. Branchless functions
  still require behavioral tests. See “Coverage minimum versus approved target” for the
  constitutional floor and unchanged project policy.
- **Static configuration**: mypy targets Python 3.12, strict mode, warn_unused_ignores,
  warn_unreachable and disallow_any_unimported; reject broad ignored imports and unexplained
  casts/Any/suppressions. Isolate justified library typing gaps to checked adapter bridges. Ruff
  targets py312 with E4/E7/E9, F, I, B and UP rules plus format --check. Import Linter and
  architecture tests above are mandatory. Pin all configurations/versions in pyproject.toml and
  uv.lock. None is only an editor recommendation.

### Failure contracts — Constitution v2.0.0 alignment

Expected validation failures and business rejections MUST be returned contractual outcomes. This
applies to existing identifier validation and enrollment conflict handling as well as the
Student details extension. Exception-based expected paths in the current implementation are
migration work, not accepted design exceptions.

- **Domain validation**: expose result-returning factories for identifiers, required text, and
  records built from untrusted values. A factory returns the valid Domain value or a typed
  validation failure; it MUST NOT construct an invalid object and catch a constructor exception
  as routine validation. Domain owns the validation predicates and applies them during
  construction, restoration and transitions. Guarded constructors may raise for internal misuse
  of their valid-value contract; callers MUST NOT use those guards as input parsers or translate
  programming errors into business outcomes. Student and Enrollment factories preserve record
  invariants.
- **Application validation**: coordinate factories and branch on their outcomes before invoking
  operations requiring valid values. Preserve verification -> target-ID validation -> ownership
  -> course-ID validation -> ordered prerequisite/policy checks. Student provisioning validates
  IDs, then name, then email and returns the first invalid field. Error accumulation is
  permitted by the constitution but not selected for this feature; FR-009 remains exactly
  first-match. No duplicate validation rules in Application and no blanket ValueError/TypeError
  catch to return INVALID_REQUEST.
- **Expected port outcomes**: repository reads return a valid record or None for absence.
  IdentityVerifier returns VerifiedIdentity or None for negative verification. Enrollment add
  returns Added | PairConflict; Student insert/replace returns Saved | EmailKeyConflict. These
  are Core-owned values, never exception subclasses. Ports do not return transport enums or
  infrastructure exception objects.
- **Conflict coordination**: PairConflict causes rollback/close and at most one fresh full
  ordered enrollment attempt, preserving FR-009 precedence. A second conflict is a technical
  StorageFailure, not an unverified ALREADY_ENROLLED assertion. EmailKeyConflict is a precise
  persistence fact translated by Application into the Domain email-conflict outcome; unrelated
  integrity errors MUST NOT become conflicts. Adapters may catch the database driver's precise
  constraint exception to implement these outcome contracts; that exception MUST NOT cross the
  port boundary.
- **Unexpected failures**: adapters translate only documented database/row-corruption failures
  to Application-owned StorageFailure, and documented provider operational failures to
  IdentityUnavailable. These technical exceptions remain permitted; Application translates them
  to PERSISTENCE_FAILURE/StudentStorageFailure result or IDENTITY_UNAVAILABLE respectively,
  never DENIED, missing-record, invalid-input, or email-conflict results. Student operation's
  StudentStorageFailure result and the technical exception are distinct types, even if existing
  terminology overlaps. Unexpected programming/contract exceptions propagate to the outer
  host/transport error handler and become sanitized internal errors with diagnostic recording;
  no broad catch in a validator, verifier or use case reclassifies them as business rejections
  or provider outages. Raw exception detail remains outside public output.
- **Cleanup**: rollback active work and close on rejection/exception; do not mask the primary
  failure with cleanup failure. A technical cleanup failure must be recorded and must not become
  a business rejection or delete a confirmed committed record.

**Migration and verification**: replace current Application catches of constructor ValueError
and UniqueConflict with typed-result branches; remove UniqueConflict as an exception port
contract. Narrow the identity adapter's broad Exception catch to its documented operational
failures. Persistence row decoding must inspect factory results explicitly rather than catch
arbitrary ValueError from converter code; an invalid provider representation is a technical
boundary-contract failure, while unrelated converter/programming defects propagate. Update
affected contracts, doubles and tests; keep public GraphQL SDL/reason names and HTTP semantics
unchanged. Group changed behaviors into cohesive acceptance-guided increments with relevant
behavioral Red before implementation and Green afterward, including invalid raw IDs, invalid
text, conflicts, provider outages, corrupt stored rows, and injected programming errors. Factory
results and port conflict branches join complete Core coverage. Final design assessment
and remaining implementation obligations are recorded at the end of this plan.

## Project Structure

### Documentation (this feature)

```text
specs/001-enroll-course/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── enrollment-api.md
│   ├── schema.graphqls
│   └── student-details.md
└── evidence/                 # created during implementation
```

`tasks.md` is generated by the subsequent tasks workflow, not this command.

### Source Code (planned repository root)

```text
pyproject.toml
uv.lock
src/enrollment/
├── domain/                  # validated IDs, records, policies, Enrollment, reasons
├── application/             # FR-009 orchestration, missing-record results, owned ports
├── adapters/
│   ├── graphql/             # core schema/resolver wiring, output conversion, SDL
│   ├── http/                # Flask app factory/routes, request and response conversion
│   ├── persistence/         # sqlite3 UoW, row/error conversion
│   └── identity/            # external verifier bridge
└── bootstrap.py             # composition / exported Flask WSGI application
tests/
├── acceptance/
├── domain/
├── application/
├── adapters/
└── architecture/
scripts/check-quality.sh
```

**Structure Decision**: One package, process and database preserve a small deployment. The HTTP
adapter may depend on the GraphQL execution adapter as an explicit composed inbound pipeline;
other sibling adapters remain independent. Core still depends on neither. The runtime packaged
SDL must equal the design contract after normalization. These application paths already exist.
Extend them without replacing the implemented enrollment flow.

## Phase 0: Research Outcome

[research.md](research.md) records the required Python choice, graphql-core/Flask selection,
typing and bridges, sqlite3 transaction mechanics, verification strategy and alternatives. No
applicable planning clarification remains unresolved. Stable dependency resolution and runtime
checks remain implementation obligations.

## Phase 1: Design Outcome

[data-model.md](data-model.md), [contracts/enrollment-api.md](contracts/enrollment-api.md) and
[quickstart.md](quickstart.md) use Python with Application-owned repository existence checks and
Domain-owned policies. [contracts/schema.graphqls](contracts/schema.graphqls) is unchanged
because the public GraphQL contract is language independent. Post-design gates pass at design
level. Stop before task generation or implementation.

## Student Details Design

### Scope and implementation baseline

The implementation baseline predates required Student details: Student and its stored
representation contain student_id/programme_id. Reassess the working tree before implementation
rather than treating this baseline as a live completion audit. Add required name/email without
defaults. Existing constructors, repository doubles, direct SQL, seeds, README host guidance and
installed schema-resource tests must be adapted. Historical tasks/evidence do not establish
completion of this extension. Reconcile remaining tasks with current source, preserve completed
work, and retain original execution records.

### Responsibilities and acceptance boundaries

- Domain: add frozen StudentName and StudentEmail values in domain/values.py, validating actual
  string type and at least one non-whitespace character. Preserve supplied text. Student
  requires these values and rejects wrong types during construction/reconstitution/replacement.
  StudentEmail exposes the whole-text casefold comparison key. Domain owns the
  email-availability policy, including self-exclusion, and typed invalid-detail/email-conflict
  reasons.
- Application: add an internal student-record integration operation in
  application/student_details.py with separate Application-owned student-record UoW Protocols.
  It accepts raw ID/programme/name/email input for create or replace, obtains valid Domain
  values through result-returning factories, loads a conflicting owner by email key, invokes the
  Domain uniqueness policy, saves and commits. Missing replacement target yields a typed
  missing-student result; create for an existing ID yields a separate existing-student result.
  Neither is an email conflict. No programme existence prerequisite is added; dangling programme
  references remain representable. This operation is a host integration boundary, with no new
  HTTP/GraphQL management interface or authentication flow.
- Persistence: extend schema.sql and row conversion; implement the separate student-record UoW
  in the existing persistence adapter. Keep enrollment UoW write capabilities limited to
  Enrollment. Use BEGIN IMMEDIATE before conflict lookup and save, explicit rollback/commit, and
  specific error translation. No adapter selects Domain email policy or orchestrates the whole
  operation.
- Acceptance: preserve Flask POST /graphql for User Story 1. For User Story 2, call the public
  Python integration operation with real temporary SQLite and observe returned result plus
  reopened stored state; no HTTP management route is invented. Cohesive increments begin with
  relevant executed behavioral Red, guided by acceptance tests; focused layer tests are added
  where needed. Shared boundary tests may cover multiple layers. Reconstitution also has direct
  Domain/adapter tests; corrupted persisted Student data remains PERSISTENCE_FAILURE during
  enrollment, never MISSING_STUDENT or a new FR-009 business step.

### Email comparison and storage integrity

Use Python 3.12 Unicode str.casefold() on the complete supplied address. Preserve original
spelling; do not trim, parse, validate email syntax, normalize Unicode composition, or apply
provider alias rules. Nonblank uses Python whitespace semantics (value.strip() only as a
validity predicate); names need not be unique. Casefold expansions are included, e.g.
Straße@example.com conflicts with STRASSE@EXAMPLE.COM. Leading/trailing spaces remain
significant under the specification's existing assumption.

Register deterministic SQL functions for required-text validity and email comparison through one
adapter connection setup helper, delegating to public Domain mechanisms. Add NOT
NULL/TEXT/nonblank constraints to name/email and a unique expression index `students_email_key`
on the Domain-derived email key. All enrollment, initialization, integration and fixture
connections must register the functions before accessing the schema. Missing registration must
fail closed; no fallback to SQLite NOCASE or lower(). An expression index prevents a caller from
supplying a forged separate key. Concurrent writers serialize and the unique index remains the
final guard. Recognize only that index's unique conflict as EmailConflict; other constraints and
SQL errors remain distinct technical failures. No INSERT OR REPLACE/IGNORE.

### Value equality and entity identity

StudentEmail is an immutable value object. Two StudentEmail instances are equal if and only if
their complete supplied email strings have equal Unicode `str.casefold()` keys. Preserve
original spelling for display/storage; it does not participate separately in equality. Implement
equality and hashing together rather than use default dataclass field equality/hash over the
original spelling. `hash(email)` is derived from that same comparison key, so equal values
always have equal hashes. Hashes are process-local collection behavior, never persisted keys or
stable identifiers.

Equality is supported only between StudentEmail instances. For other operand types, `__eq__`
returns NotImplemented; do not coerce strings, StudentName, or other objects into emails.
Inequality follows the same value semantics. Domain owns the comparison key used by equality,
hashing, the uniqueness policy and persistence indexing, so these mechanisms cannot disagree. No
trimming, Unicode normalization, syntax rules, provider aliases, or partial-address comparison
is added.

Student entity identity and entity equality remain based exclusively on StudentId. Changing
name/email/programme does not change that identity; two distinct StudentIds never become the
same Student because their emails compare equal. If Student is hashable, hash by immutable
StudentId consistently; email must never enter its hash. Email uniqueness remains a separate
Domain rule backed by atomic persistence.

### Compatibility and delivery sequence

No automatic migration/backfill is included: there are no trustworthy names/emails to invent for
old rows. Initialization must detect an existing legacy students shape and fail clearly without
altering it; runtime read failure is sanitized. Hosts provision a new schema with valid records
or perform their own audited migration before upgrade. Re-running initialization on the
compatible new schema remains idempotent and preserves rows. Test both paths. Centralize
production schema use for valid fixtures; isolate intentionally corrupt/legacy schemas to
explicit tests. Use named INSERT columns.

Sequence for subsequent tasks: acceptance Red for required details -> Domain text values/Student
invariants -> schema, connection registration and reconstitution -> internal integration and
uniqueness policy with concurrent-claim Red -> fixture/regression updates -> evidence-gate
extension -> final checks. Each cohesive increment requires relevant behavioral Red before
implementation and Green afterward. Related behaviors may share a cycle and tests may span
layers; a broad failure counts only when it demonstrates the behavior required by that coherent
increment. Missing constructor parameters/import failures alone do not count as behavioral Red.
No tasks or implementation are produced by this planning command.

### Extension verification

Preserve the 15 enrollment and seven Student-detail acceptance scenario families, including
parameter variants, with explicit test identities rather than count-only checks. Reject missing
or skipped required scenarios and ambiguous duplicate identity mappings. Cover required text,
reconstitution, uniqueness, integration, equality and entity identity through cohesive
increments and appropriate automated tests.

Keep public HTTP/GraphQL signatures and enrollment reason names unchanged. Apply the
architecture and coverage policies below to every new module and affected function. Final
acceptance/regression, static, architecture, coverage and contract checks must run against the
final implementation. Historical green results do not verify new work.

## Execution Evidence and Verification

### Execution evidence and tooling migration

Preserve architecture, runtime dependencies, business scope, contracts and approved quality
gates. The working-tree recorder/validator currently requires a prospective protocol with source
snapshots, per-behavior mappings/reviews and mandatory REFACTOR/NO_REFACTOR stages. Its recorder
requires `EVIDENCE_REQUEST` JSON and uppercase stages; earlier lowercase examples without a
request are incompatible. These tools need implementation changes before they conform to the
design below.

#### Process enforcement removal and lightweight replacement

The implementation phase MUST remove mechanisms whose sole purpose is enforcing per-behavior
process ceremony. Remove mandatory source blob/snapshot storage and transition comparison,
global event hash chains/contiguous-event restrictions, per-behavior test/task maps, fixed
historical increment inventories as completion criteria, and mandatory REFACTOR/NO_REFACTOR
artifacts or per-behavior approvals. Remove associated protocol-only fixtures and configuration
once unused; do not keep them as an alternative mandatory path. Keep content hashes/final
digests where they serve final-result integrity rather than intermediate process policing.

Replace that machinery with one consolidated run log or equivalent small set of records
containing actual test commands, relevant test identities, output or a result reference, exit
result, and sufficient chronological context to associate behavioral Red before implementation
and Green afterward with a cohesive increment. One record may reference several coherent
increments; one increment may cover several related behaviors or layers. An ordinary review note
may explain the grouping and refactor consideration; no dedicated approval/no-refactor artifact
is mandatory. Do not demand a custom storage format as constitutional proof. Final review
remains mandatory and MUST inspect the execution evidence rather than infer TDD from Green.

Migration verification MUST show valid consolidated evidence is accepted without snapshots, hash
chains or no-refactor approvals; missing behavioral Red, failing Green, environmental-only
failure and stale final checks are rejected. Preserve required acceptance identities
independently from the optional organization of TDD increments. Historical richer evidence
remains readable or directly referenceable; removing its enforcement machinery MUST NOT delete
or rewrite the evidence files.

### Architecture fitness simplification

| Responsibility | Primary verification after simplification | Protection retained |
|---|---|---|
| Dependency direction and adapter independence | Existing Import Linter contracts | Domain cannot import Application; Core cannot import adapters; declared HTTP-to-GraphQL composition remains allowed |
| Domain/framework and Core boundary type isolation | Import contracts plus targeted public-signature/annotation checks | Resolve aliases/nested types and inspect relevant methods/re-exports; forbid external framework, persistence and provider types |
| Dynamic dependency escapes | Small targeted check where static graph cannot enforce isolation | Reject dynamic loading that bypasses Core restrictions |
| Semantic boundary conversion | Focused converter/contract and acceptance tests | Invalid external representations cannot become valid Domain state; expected versus technical failures remain distinct |
| Business ownership and sequencing | Domain/Application behavioral tests and meaningful port/policy spies | Application coordinates; Domain decides; first-match short circuits remain exact |

Avoid a second general import-graph implementation. Remove overlapping AST import rules only
after allowed/violating fixtures demonstrate coverage through the primary checker or a focused
retained gap check. The existing exact `policies` call-set and source-name/comparison-string
assertions are implementation-coupled; replace their responsibility claims with behavioral tests
before deleting them. Consolidate fixtures by distinct failure mode, not by each spelling of the
same rule. Keep architecture checks automated, non-vacuous, recursive over new modules, and
mandatory in final quality execution. Simplification does not authorize new dependency
exceptions or weaker Domain isolation. Static import checks alone cannot prove semantic
conversion.

### Coverage minimum versus approved target

| Policy source | Scope and measurement | Decision for this update |
|---|---|---|
| Constitution IV minimum | 100% branch coverage for every whole new/changed business-logic function or method, including unchanged measurable branches; branchless functions still need behavioral tests | Mandatory floor; no changed-line approximation or exclusions hiding business behavior |
| Approved feature/project gate | coverage.py `branch=true`, complete Domain/Application source directories including unimported modules, `fail_under=100`: 100% statement and branch coverage, plus business behavior elsewhere | Retain unchanged; stronger than the constitutional floor |

The current complete-Core target, no-business-exclusion policy, strict static checks,
architecture checks, required acceptance/regression scenarios and contract verification remain
approved gates. This update does not reduce measured scope, percentage or exclusions. Any future
relaxation of a project-specific target requires a separate, explicit Project Owner decision and
impact review, and can never breach the constitutional floor. Final check freshness remains
mandatory even though intermediate snapshots and per-behavior execution histories are removed.

### Historical evidence reassessment

The historical review rejected grouped Red suites followed by grouped implementations under the
former per-behavior rule. Grouping alone is no longer a violation. Review the original
commands/results and changed responsibilities for coherent implementation units and actual
behavioral failure before implementation and success afterward. Exclude
import/configuration/socket-permission failures as Red. Do not fabricate failures, edit
historical transcripts, or infer TDD from coverage. Record a new review decision with concrete
references; unresolved evidence gaps remain reported. This planning update does not change
`review.json`, close C1, complete T050, or certify final implementation compliance.

### Delivery order and post-design assessment

Reconcile existing tasks first. Migrate evidence recording/validation before using it as a gate
for new behavior; consolidate fitness checks with equivalent protection; implement remaining
failure-contract and Student-detail changes in cohesive acceptance-guided increments; reassess
historical evidence; run all mandatory final checks and completion review. Refactor-only tooling
cleanup starts from passing relevant tests; new or changed behavior follows the TDD policy
above.

Principles I–V PASS at design level under Constitution v2.0.0, with no exceptions.
Implementation conformity remains unverified pending these changes, historical review and final
checks. This planning command does not implement code, regenerate tasks, close C1/T050 or
certify completion. The next workflow is `$speckit-tasks`.

## Complexity Tracking

No constitutional violations or waivers. Flask handles HTTP integration; direct graphql-core
keeps GraphQL schema/resolver wiring explicit. Both stay in inbound adapters with behavioral
tests. WSGI serving matches synchronous sqlite3 and avoids async coordination machinery; no
additional external infrastructure is required.
