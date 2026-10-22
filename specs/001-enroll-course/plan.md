# Implementation Plan: Student Self-Enrollment

**Branch**: `001-enroll-course` | **Date**: 2026-10-21 | **Spec**: [spec.md](spec.md)

**Input**: `specs/001-enroll-course/spec.md`; Project Owner requires Python as the development language, graphql-core as the GraphQL engine, and Flask as the HTTP Transport Adapter. Application owns repository absence handling and exact FR-009 sequencing; Domain owns business policies and invariants.

## Summary

Implement with Python 3.12, graphql-core SDL-first GraphQL, Flask as the synchronous HTTP Transport Adapter, Waitress WSGI serving and embedded sqlite3 persistence. Framework-free Domain owns self-enrollment authorization, duplicate-enrollment and offering-eligibility policies and Enrollment invariants; Application handles failed identity verification and repository misses and orchestrates FR-009 through owned ports; adapters perform explicit boundary conversions. The owner selects Python, graphql-core and Flask directly. Preserve FR-001–FR-010 and all fifteen enrollment acceptance scenarios; extend Student for FR-011–FR-013, User Story 2 scenarios 1–7, and SC-005–SC-007 alongside SC-001–SC-004 and Constitution v1.4.0.

## Technical Context

**Language/Version**: Python 3.12; declare >=3.12,<3.13 for the initial supported/tested runtime. No Java build/runtime dependency.

**Primary Dependencies**: graphql-core (>=3.3,<3.4; import package `graphql`) with Flask (>=3.1,<3.2) and Waitress at runtime plus Python standard library (`sqlite3`, `dataclasses`, `typing`). Development: pytest, HTTPX for real socket tests, coverage.py, mypy, Ruff and Import Linter. Retain existing pyproject.toml and committed uv.lock for this extension; no dependency upgrade is required.

**Storage**: Local file-backed SQLite, five persisted record types, one immediate transaction/connection per enrollment. No ORM or database server.

**Testing**: pytest; Flask's test client exercises HTTP POST `/graphql` with real GraphQL documents, JSON and credential headers. Acceptance uses real SQLite and an injected deterministic verifier. Add real local Waitress socket smoke/concurrency tests. Focused Domain/Application, adapter, schema and architecture tests complement acceptance.

**Target Platform**: Python 3.12 on Linux, one threaded WSGI process and local database. Each request creates/uses/closes its connection in the same worker; no global connection or async offload needed.

**Project Type**: One Python package with GraphQL HTTP enrollment and an internal host student-record integration operation.

**Performance Goals**: No latency, throughput or volume targets specified. SQLite serializes writers; no distributed deployment or performance guarantee is introduced.

**Constraints**: Exact FR-009 precedence, generic identity denial before persistence, save-time eligibility, pair uniqueness, commit before success, no mutation caused by rejection. Five-second bounded lock wait maps to technical failure. Production identity verification and prerequisite-management interfaces remain externally supplied; internal student-record integration enforces the new invariants.

**Scale/Scope**: Five persisted record types, one GraphQL mutation, and an internal student-record integration operation; query-root placeholder is schema scaffolding. No UI, management operations, capacity, terms, fees, withdrawal, federation, subscriptions, broker, containers or extra services.

## Constitution Check

*GATE: assessed before Phase 0; re-evaluated after Phase 1. PASS means design conformity with implementation obligations, not executed application checks.*

| Principle | Before research | Post-design obligation |
|---|---|---|
| I. Inward dependencies | PASS: Python supports owned ports and adapters | PASS: Import Linter and architecture/signature tests enforce inward dependencies, Core independence and no framework/persistence leakage |
| II. Domain integrity / Full Bridge | PASS: Domain retains policies; Application handles repository misses | PASS: explicit expected-failure results, Domain-owned validating factories, separate technical exception contracts, Application first-match sequencing and invariant-safe construction/reconstitution; explicit GraphQL/provider/row/outcome conversion; no redundant Application–Domain mappings |
| III. Outside-In TDD | PASS: public boundary declared | PASS: pytest HTTP acceptance drives executed behavioral Red/Green/Refactor; real persistence, identity double and retained evidence |
| IV. Fitness / coverage | PASS: enforcement strategy selected | PASS: complete Core source scope at 100% statement-and-branch coverage, including whole affected functions; branchless behavioral tests; negative fitness fixtures |
| V. Evidence / quality | PASS: final-state review required | PASS: pytest, coverage, mypy, Ruff, Import Linter, architecture and evidence checks must run and pass on final implementation state |

No deviations or constitutional exceptions. No implementation checks are claimed to have passed during planning.

### Resolved constitutional planning questions

- **Boundary contracts**: Keep [SDL](contracts/schema.graphqls) and [contract](contracts/enrollment-api.md). Flask/Werkzeug request/response/context proxies, graphql-core execution context/types, WSGI environ, HTTPX objects, sqlite3 rows/connections/exceptions and identity SDK types stay outside Core. Commands can contain raw invalid input; Domain factories return explicit validation outcomes before guarded construction of valid state. Adapters may directly call public Domain constructors for technical adaptation without orchestrating the use case. Application may directly use Domain values; no redundant mapping solely for layering.
- **Port ownership / context**: One Enrollment context. Application owns IdentityVerifier and EnrollmentUnitOfWork/Factory Protocols because orchestration needs them. Domain needs no external capability port. No cross-context messaging or distributed transactions.
- **Transaction coordination**: Application invokes its IdentityVerifier port. A failed verification returns the Core-defined DENIED immediately, without a Domain ownership call or persistence. On success it passes the trusted VerifiedIdentity and validated target StudentId to Domain ownership policy; mismatch returns DENIED before persistence. It loads Student, Programme and Course sequentially, handles each absent repository result by immediately returning its Core-defined missing-record rejection, and calls Domain duplicate and offering-eligibility policies only when their prerequisite records exist. It creates Enrollment through Domain, adds and commits through the port, then returns success. No trivial Domain existence guards or duplicate Application business predicates are introduced. The sqlite3 adapter implements explicit SQL BEGIN IMMEDIATE/COMMIT/ROLLBACK with autocommit=True and closes its worker-owned connection. No SQL or business predicates in the GraphQL resolver.
- **Rejection ownership and ordering**: Application owns FR-009 sequencing: unverified identity -> non-owner -> missing Student -> missing Programme -> missing Course -> already enrolled -> course not offered. Application handles unverified identity at stage 1; Domain ownership decides mismatch at stage 2 only after verification succeeds. Neither denial accesses persistence. Application handles repository absence for the next three; Domain decides duplicate and offering eligibility when reached. Application may branch on typed Domain outcomes to short-circuit but must not recalculate their predicates. Missing-record rejection types live in Application Core contracts; Domain policy reasons remain in Domain and are used directly in the Application result union. Domain never imports Application result types.
- **Verification boundary**: IdentityVerifier is Application-owned; its ordinary result is trusted Domain VerifiedIdentity or None when credentials do not establish a verified identity. Application returns the same Core DENIED on None without invoking ownership or opening a UoW. Domain ownership accepts only VerifiedIdentity and StudentId; it neither calls IdentityVerifier nor depends on any verification port or UnverifiedIdentity model. The Core Denied value/type can remain Domain-defined and be reused by Application, preserving inward dependencies and the identical public denial. Existing provider-unavailability technical failures remain distinct from a negative verification result and also short-circuit before Domain/persistence.
- **GraphQL/HTTP ownership**: graphql-core is the schema/execution engine, not an HTTP application/server. Flask owns HTTP routing, request parsing and response construction. Its adapter owns, method/content/envelope checks, credentials/context, execution invocation and sanitized JSON responses; Waitress owns sockets/workers. Bootstrap injects the GraphQL executor and Application dependencies into a Flask app factory; no Flask context is passed inward. GraphQL wiring owns SDL binding, explicit union type names and output conversions. Build schema/wiring once, then avoid per-request schema mutation. Engine objects stay inside inbound adapters. These technical responsibilities are driven by failing adapter tests.
- **Flask lifecycle**: An app factory configures dependencies and routes once. The synchronous POST /graphql view extracts JSON and credentials, invokes the injected GraphQL adapter and formats JSON responses. Keep Flask request/current_app/g/session proxies and Werkzeug types out of Domain, Application and GraphQL resolver contracts. Use an adapter-owned plain execution context. Preserve the POST-only protocol by disabling automatic OPTIONS for this route and the unused static route. HTTP error handlers preserve status/Allow headers and return sanitized JSON; do not turn unexpected errors into success.
- **Application frameworks**: Choose no framework dependencies in Core for this feature. This does not amend the constitution's general permission for appropriate Application frameworks. Dataclasses, enums and typing are standard-library mechanisms; Flask/graphql-core/Waitress/HTTP and database modules remain adapters/bootstrap.
- **Fitness scope**: Import Linter layers order bootstrap -> adapters -> application -> domain, explicitly permitting adapters to use public Domain types. Forbid outward dependencies, cycles, unrelated sibling adapter coupling and external framework/persistence/provider imports in Core, including re-exports and annotation imports. Include external-package graphs for forbidden-import contracts. AST/signature tests inspect public contracts, resolve aliases and reject external types/unchecked Any; forbid dynamic-import escape hatches in Core. Fail empty scope/scans. Violating fixtures prove detection. Semantic leakage through data containers requires converter tests and review, beyond import rules.
- **TDD scope**: Every independently testable business/adapter behavior begins with an executed expected behavioral failure. Acceptance guides inner tests; broad tests may drive multiple layers if their failures demonstrate each changed responsibility. Configuration/documentation validation does not require artificial Red. Pure refactors begin green and rerun relevant checks. Import/configuration errors are not behavioral Red. Do not weaken tests merely to make code pass.
- **Approval**: Project Owner remains specification/change and future exclusion approval authority. The existing ready-for-planning spec is the baseline. Python selection is explicitly authorized; the updated spec authorizes the Student detail extension; this plan is aligned with the current Constitution v1.4.0; no new ratification claim is made.
- **Evidence**: Retain commands, stdout/stderr, exit codes, execution order, test identity and source revision plus working-tree diff digest under `specs/001-enroll-course/evidence/<increment>/`. Preserve Red before production change, Green after minimum behavior, Refactor passing tests or no-refactor rationale. Final manifest binds mandatory checks to source/config/test digest excluding evidence/build output. Later edits invalidate affected results and final gates rerun. Reviewer inspects transcripts, not summaries alone.
- **Coverage scope**: Entire `src/enrollment/domain/` and `src/enrollment/application/`, including constructors, reconstitution, Domain invariant/authorization/duplicate/eligibility policies, Application identity-verification and repository absence branches, result decisions and orchestration. coverage.py branch=True and fail_under=100 across complete source directories is stronger than the whole-function branch minimum and covers unchanged branches too. Audit discovery of unimported files and default/custom exclusions; no business omissions or no-cover/no-branch suppressions. Include any business behavior introduced elsewhere. No-branch functions require behavior tests. Technical wiring/tooling may remain outside the business threshold only while free of business decisions; all adapter responsibilities still require tests.
- **Static configuration**: mypy targets Python 3.12, strict mode, warn_unused_ignores, warn_unreachable and disallow_any_unimported; reject broad ignored imports and unexplained casts/Any/suppressions. Isolate justified library typing gaps to checked adapter bridges. Ruff targets py312 with E4/E7/E9, F, I, B and UP rules plus format --check. Import Linter and architecture tests above are mandatory. Pin all configurations/versions in pyproject.toml and uv.lock. None is only an editor recommendation.

### Failure contracts — Constitution v1.4.0 alignment

Expected validation failures and business rejections MUST be returned contractual
outcomes. This applies to existing identifier validation and enrollment conflict
handling as well as the Student details extension. Exception-based expected paths
in the current implementation are migration work, not accepted design exceptions.

- **Domain validation**: expose result-returning factories for identifiers, required
  text, and records built from untrusted values. A factory returns the valid Domain
  value or a typed validation failure; it MUST NOT construct an invalid object and
  catch a constructor exception as routine validation. Domain owns the validation
  predicates and applies them during construction, restoration and transitions.
  Guarded constructors may raise for internal misuse of their valid-value contract;
  callers MUST NOT use those guards as input parsers or translate programming errors
  into business outcomes. Student and Enrollment factories preserve record invariants.
- **Application validation**: coordinate factories and branch on their outcomes before
  invoking operations requiring valid values. Preserve verification -> target-ID
  validation -> ownership -> course-ID validation -> ordered prerequisite/policy checks.
  Student provisioning validates IDs, then name, then email and returns the first
  invalid field. Error accumulation is permitted by the constitution but not selected
  for this feature; FR-009 remains exactly first-match. No duplicate validation rules
  in Application and no blanket ValueError/TypeError catch to return INVALID_REQUEST.
- **Expected port outcomes**: repository reads return a valid record or None for
  absence. IdentityVerifier returns VerifiedIdentity or None for negative verification.
  Enrollment add returns Added | PairConflict; Student insert/replace returns
  Saved | EmailKeyConflict. These are Core-owned values, never exception subclasses.
  Ports do not return transport enums or infrastructure exception objects.
- **Conflict coordination**: PairConflict causes rollback/close and at most one fresh
  full ordered enrollment attempt, preserving FR-009 precedence. A second conflict
  is a technical StorageFailure, not an unverified ALREADY_ENROLLED assertion.
  EmailKeyConflict is a precise persistence fact translated by Application into the
  Domain email-conflict outcome; unrelated integrity errors MUST NOT become conflicts.
  Adapters may catch the database driver's precise constraint exception to implement
  these outcome contracts; that exception MUST NOT cross the port boundary.
- **Unexpected failures**: adapters translate only documented database/row-corruption
  failures to Application-owned StorageFailure, and documented provider operational
  failures to IdentityUnavailable. These technical exceptions remain permitted;
  Application translates them to PERSISTENCE_FAILURE/StudentStorageFailure result or
  IDENTITY_UNAVAILABLE respectively, never DENIED, missing-record, invalid-input,
  or email-conflict results. Student operation's StudentStorageFailure result and the
  technical exception are distinct types, even if existing terminology overlaps.
  Unexpected programming/contract exceptions propagate to the outer host/transport
  error handler and become sanitized internal errors with diagnostic recording;
  no broad catch in a validator, verifier or use case reclassifies them as business
  rejections or provider outages. Raw exception detail remains outside public output.
- **Cleanup**: rollback active work and close on rejection/exception; do not mask the
  primary failure with cleanup failure. A technical cleanup failure must be recorded
  and must not become a business rejection or delete a confirmed committed record.

**Migration and verification**: replace current Application catches of constructor
ValueError and UniqueConflict with typed-result branches; remove UniqueConflict as
an exception port contract. Narrow the identity adapter's broad Exception catch to
its documented operational failures. Persistence row decoding must inspect factory
results explicitly rather than catch arbitrary ValueError from converter code; an
invalid provider representation is a technical boundary-contract failure, while
unrelated converter/programming defects propagate. Update affected contracts, doubles and tests;
keep public GraphQL SDL/reason names and HTTP semantics unchanged. Drive each changed
behavior with fresh acceptance/inner Red evidence, including invalid raw IDs, invalid
text, conflicts, provider outages, corrupt stored rows, and injected programming
errors. Factory results and port conflict branches join complete Core coverage.
Post-design Principles I–V: PASS at design level; implementation conformity remains
unverified until the new work and mandatory checks are complete.

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

**Structure Decision**: One package, process and database preserve a small deployment. The HTTP adapter may depend on the GraphQL execution adapter as an explicit composed inbound pipeline; other sibling adapters remain independent. Core still depends on neither. The runtime packaged SDL must equal the design contract after normalization. These application paths already exist. Extend them without replacing the implemented enrollment flow.

## Phase 0: Research Outcome

[research.md](research.md) records the required Python choice, graphql-core/Flask selection, typing and bridges, sqlite3 transaction mechanics, verification strategy and alternatives. No applicable planning clarification remains unresolved. Stable dependency resolution and runtime checks remain implementation obligations.

## Phase 1: Design Outcome

[data-model.md](data-model.md), [contracts/enrollment-api.md](contracts/enrollment-api.md) and [quickstart.md](quickstart.md) use Python with Application-owned repository existence checks and Domain-owned policies. [contracts/schema.graphqls](contracts/schema.graphqls) is unchanged because the public GraphQL contract is language independent. Post-design gates pass at design level. Stop before task generation or implementation.

## Student Details Extension — 2026-10-21

### Scope and existing implementation

The current Student dataclass and students table contain only student_id/programme_id; Session.student reconstitutes that shape. Add required name/email without defaults. Existing constructors, repository doubles, direct SQL, seeds, README host guidance and installed schema-resource tests must be adapted. Existing tasks/evidence describe the earlier implementation; they do not establish completion of this extension. Task generation must append new work rather than mark historical tasks incomplete or reuse old Red evidence.

### Responsibilities and acceptance boundaries

- Domain: add frozen StudentName and StudentEmail values in domain/values.py, validating actual string type and at least one non-whitespace character. Preserve supplied text. Student requires these values and rejects wrong types during construction/reconstitution/replacement. StudentEmail exposes the whole-text casefold comparison key. Domain owns the email-availability policy, including self-exclusion, and typed invalid-detail/email-conflict reasons.
- Application: add an internal student-record integration operation in application/student_details.py with separate Application-owned student-record UoW Protocols. It accepts raw ID/programme/name/email input for create or replace, obtains valid Domain values through result-returning factories, loads a conflicting owner by email key, invokes the Domain uniqueness policy, saves and commits. Missing replacement target yields a typed missing-student result; create for an existing ID yields a separate existing-student result. Neither is an email conflict. No programme existence prerequisite is added; dangling programme references remain representable. This operation is a host integration boundary, with no new HTTP/GraphQL management interface or authentication flow.
- Persistence: extend schema.sql and row conversion; implement the separate student-record UoW in the existing persistence adapter. Keep enrollment UoW write capabilities limited to Enrollment. Use BEGIN IMMEDIATE before conflict lookup and save, explicit rollback/commit, and specific error translation. No adapter selects Domain email policy or orchestrates the whole operation.
- Acceptance: preserve Flask POST /graphql for User Story 1. For User Story 2, call the public Python integration operation with real temporary SQLite and observe returned result plus reopened stored state; no HTTP management route is invented. Each new behavior begins with an executed failing acceptance test, followed by layer tests as needed. Reconstitution also has direct Domain/adapter tests; corrupted persisted Student data remains PERSISTENCE_FAILURE during enrollment, never MISSING_STUDENT or a new FR-009 business step.

### Email comparison and storage integrity

Use Python 3.12 Unicode str.casefold() on the complete supplied address. Preserve original spelling; do not trim, parse, validate email syntax, normalize Unicode composition, or apply provider alias rules. Nonblank uses Python whitespace semantics (value.strip() only as a validity predicate); names need not be unique. Casefold expansions are included, e.g. Straße@example.com conflicts with STRASSE@EXAMPLE.COM. Leading/trailing spaces remain significant under the specification's existing assumption.

Register deterministic SQL functions for required-text validity and email comparison through one adapter connection setup helper, delegating to public Domain mechanisms. Add NOT NULL/TEXT/nonblank constraints to name/email and a unique expression index `students_email_key` on the Domain-derived email key. All enrollment, initialization, integration and fixture connections must register the functions before accessing the schema. Missing registration must fail closed; no fallback to SQLite NOCASE or lower(). An expression index prevents a caller from supplying a forged separate key. Concurrent writers serialize and the unique index remains the final guard. Recognize only that index's unique conflict as EmailConflict; other constraints and SQL errors remain distinct technical failures. No INSERT OR REPLACE/IGNORE.

### Compatibility and delivery sequence

No automatic migration/backfill is included: there are no trustworthy names/emails to invent for old rows. Initialization must detect an existing legacy students shape and fail clearly without altering it; runtime read failure is sanitized. Hosts provision a new schema with valid records or perform their own audited migration before upgrade. Re-running initialization on the compatible new schema remains idempotent and preserves rows. Test both paths. Centralize production schema use for valid fixtures; isolate intentionally corrupt/legacy schemas to explicit tests. Use named INSERT columns.

Sequence for subsequent tasks: acceptance Red for required details -> Domain text values/Student invariants -> schema, connection registration and reconstitution -> internal integration and uniqueness policy with concurrent-claim Red -> fixture/regression updates -> evidence-gate extension -> final checks. Every production behavior increment still requires its own behavioral Red before implementation; a broad initial failure does not replace inner-layer TDD. Missing constructor parameters/import failures alone do not count as behavioral Red. No tasks or implementation are produced by this planning command.

### Constitutional gates for the extension

Pre-research and post-design assessment: PASS at design level for Principles I–V, with no deviations. Domain contains text validation, comparison and uniqueness policy; Application coordinates a separate owned port; SQL constraints implement storage defense using Domain comparison. HTTP/GraphQL signatures and enrollment result enums remain unchanged. Existing import/type fitness tests must scan new modules and reject framework leakage. Entire Domain/Application scope, including unchanged branches of affected constructors/orchestration and new student-detail operation, remains at 100% statement and branch coverage; no new exclusions. Business logic introduced elsewhere joins measured scope.

Extend scripts/assemble_evidence.py and scripts/check_evidence.py to require both named scenario sets (15 enrollment, 7 student-details, including parameter variants) and new text/reconstitution/uniqueness/integration increments, while retaining historical enrollment evidence. Replace hard-coded enrollment-only completeness claims with explicit required test identities and reject missing/skipped/duplicate new scenarios. Add negative gate tests. Record actual Red/Green/Refactor transcripts under fresh increment IDs. Run all mandatory final checks after final source/test/config edits and inspect review notes anew; existing green evidence is historical for this extension. Planning only validates documents, not implementation gates.

## Complexity Tracking

No constitutional violations or waivers. Flask handles HTTP integration; direct graphql-core keeps GraphQL schema/resolver wiring explicit. Both stay in inbound adapters with behavioral tests. WSGI serving matches synchronous sqlite3 and avoids async coordination machinery; no additional external infrastructure is required.

## StudentEmail equality and Student identity

StudentEmail is an immutable value object. Two StudentEmail instances are equal
if and only if their complete supplied email strings have equal Unicode
`str.casefold()` keys. Preserve original spelling for display/storage; it does not
participate separately in equality. Implement equality and hashing together rather
than use default dataclass field equality/hash over the original spelling.
`hash(email)` is derived from that same comparison key, so equal values always
have equal hashes. Hashes are process-local collection behavior, never persisted
keys or stable identifiers.

Equality is supported only between StudentEmail instances. For other operand types,
`__eq__` returns NotImplemented; do not coerce strings, StudentName, or other objects
into emails. Inequality follows the same value semantics. Domain owns the comparison
key used by equality, hashing, the uniqueness policy and persistence indexing, so
these mechanisms cannot disagree. No trimming, Unicode normalization, syntax rules,
provider aliases, or partial-address comparison is added.

Student entity identity and entity equality remain based exclusively on StudentId.
Changing name/email/programme does not change that identity; two distinct StudentIds
never become the same Student because their emails compare equal. If Student is
hashable, hash by immutable StudentId consistently; email must never enter its hash.
Email uniqueness remains a separate Domain rule backed by atomic persistence.

Pre-design and post-design gates: PASS at design level under Constitution v1.4.0.
No new dependency or unresolved planning choice. Require fresh behavioral Red for
value equality, hashing, heterogeneous comparison and Student identity; include
whole affected methods in the existing complete Core coverage/evidence gates.
