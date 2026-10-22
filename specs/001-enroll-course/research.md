# Research: Python 3.12 Student Self-Enrollment

**Date**: 2026-10-22 | **Spec**: [spec.md](spec.md)

**Current baseline**: Constitution v2.3.1 is effective. [plan.md](plan.md) is the source
for feature decisions. Sections 1–14 record decisions that still apply. Where they
call v2.1.0 a proposal or point at `.specify/memory/architecture-decisions.md`,
section 15 supersedes that framing. The shared decisions file is not in this
workspace. No dependency upgrade is required.

Existing dependency selections and earlier completed migrations below remain context.
Sections 12–14 describe the source-inspected migration. Earlier descriptions of
constructor-exception and prospective-evidence machinery are historical findings,
not claims about the current working tree.

## 1. Implementation language

**Decision**: Python 3.12 is the required implementation language, following the Project Owner's explicit direction. It supersedes the previous Java recommendation. Use one Python implementation; preserve GraphQL and all enrollment requirements.

**Rationale**: The earlier comparison established that Python can satisfy the constitution. The owner's language choice settles the selection; local installation and unsupported claims about AI productivity are not reasons for it. Runtime validation, static checking, architecture fitness tests and behavioral evidence remain necessary.

**Alternatives considered**: Java 21 with Spring for GraphQL, JUnit, ArchUnit and JaCoCo remains a viable evaluated alternative but is not selected. Java nominal types and native method coverage gates offer useful feedback with more build/mapping ceremony. Python uses validated value classes, strict mypy, import/signature checks and complete-scope coverage instead. Neither language enforces the architecture, conversion semantics, TDD execution or business integrity automatically. No constitutional requirement is weakened by the owner's selection.

## 2. Direct graphql-core with Flask HTTP transport

**Decision**: Use graphql-core directly with SDL-first schema and synchronous execution; no higher-level GraphQL framework. Target the compatible stable 3.3 minor line (`>=3.3,<3.4`), pin the exact release in uv.lock, and retain Python 3.12. Use Flask (>=3.1,<3.2) as the HTTP Transport Adapter and keep Waitress for threaded WSGI serving and Flask's test client for in-process HTTP acceptance tests. Retain [schema.graphqls](contracts/schema.graphqls) unchanged.

**Rationale**: The Project Owner explicitly prefers graphql-core. It supplies schema construction, parsing, validation and execution; HTTP routing/JSON/context/error handling belong to the Flask inbound adapter, using framework utilities while retaining the explicit GraphQL contract. The package is installed as `graphql-core` and imported as `graphql`. Official [project documentation](https://github.com/graphql-python/graphql-core) lists Python 3.12 compatibility and warns minor updates may break APIs, so do not allow unconstrained minor upgrades. This choice does not change Domain or Application.

**Wiring**: Build SDL with build_schema, validate the schema, attach the mutation field's resolve callable and a union resolve_type callback returning the SDL object type name. Bind the query placeholder explicitly. Keep schema wiring immutable after initialization. Use graphql_sync with context_value, variable_values, operation_name and check_sync=True. Convert Core outcomes explicitly into adapter-owned dictionaries with GraphQL field names (`studentId`, `courseId`, `reason`), enum name strings and a trusted type tag; the union callback maps the tag to a declared output type. Do not expect snake_case Domain attributes or Python enums to match SDL automatically. Sources: [SDL and resolver binding](https://graphql-core-3.readthedocs.io/en/stable/usage/sdl.html), [execution entry points](https://graphql-core-3.readthedocs.io/en/stable/modules/graphql.html), [execution/type resolution](https://graphql-core-3.readthedocs.io/en/stable/modules/execution.html).

**HTTP integration**: A Flask app factory registers the synchronous `/graphql` route and JSON error handlers. The view checks method/media type and envelope, extracts neutral credentials, invokes the injected graphql-core adapter and constructs JSON responses. Flask request/Response/current_app/g and Werkzeug context proxies stay at this boundary; the GraphQL resolver receives only an adapter-owned plain context. graphql-core supplies neither this WSGI application nor an HTTP server. Waitress supplies sockets/workers in the same process; synchronous operations keep sqlite3 connection ownership within a worker. Flask's test client checks actual HTTP-shaped requests in process; a local socket smoke/concurrency test proves server scheduling separately. [HTTPX transports](https://www.python-httpx.org/advanced/transports/), [Waitress](https://docs.pylonsproject.org/projects/waitress/en/stable/).

**Alternatives considered**: Ariadne/Strawberry supply higher-level schema/server integration, but direct graphql-core is the owner's selection. A programmatic GraphQLSchema is possible, but keeping SDL preserves the reviewed external contract. ASGI is unnecessary for synchronous SQLite; it would require explicit blocking-I/O offload and thread ownership. The previous handwritten WSGI HTTP adapter is superseded by the owner's Flask selection. No FastAPI/Django, ORM, database server, federation, subscriptions or messaging is introduced.

**Trade-offs / verification**: More explicit transport and resolver wiring must be tested. Execute real documents/variables to verify schema validity, field mapping, union/enum names, nullability, ID coercion and all outcomes; resolver-method tests alone are insufficient. Test invalid HTTP envelopes, operationName/variables forwarding and unexpected-error sanitization. ExecutionResult.errors can carry original resolver exceptions; never serialize raw exception diagnostics or credentials. Expected business rejections remain one typed data outcome, distinct from GraphQL protocol errors. If an awaitable accidentally reaches synchronous execution, check_sync catches it; it does not create a thread or transaction. Independent workers/connections test concurrency; HTTP status alone never proves enrollment success.


**Flask decision, rationale and verification**: The owner explicitly chooses Flask for transport; graphql-core remains the engine. Use an app factory with injected executor/configuration, not a global app holding per-request identity. Flask handles request contexts and exposes a test client, while Waitress remains the HTTP server. Official [application factories](https://flask.palletsprojects.com/en/stable/patterns/appfactories/), [testing](https://flask.palletsprojects.com/en/stable/testing/), and [request contexts](https://flask.palletsprojects.com/en/stable/reqcontext/) document these roles. Flask supplies no Domain policy, transaction atomicity or TDD evidence.

Flask get_json raises 415 for a non-JSON media type and 400 for malformed JSON; do not use force/silent parsing to hide those failures. Retain independent envelope checks after parsing. Flask may otherwise generate HTML errors and automatic OPTIONS; explicitly return sanitized JSON preserving HTTP error status/headers, disable automatic OPTIONS on the POST-only route, and disable the unused static route. Sources: [Flask API](https://flask.palletsprojects.com/en/stable/api/), [error handlers](https://flask.palletsprojects.com/en/stable/errorhandling/). Test those choices rather than assuming defaults match the contract.

Use Flask's test client with JSON/header requests for acceptance. Create a separate client/request context for each concurrent worker; never carry Flask request proxies or a SQLite connection between threads. A local Waitress test with HTTPX checks sockets and scheduling; an isolated request_context alone does not run the complete dispatch pipeline. Add architecture checks forbidding Flask and Werkzeug imports/types throughout Core and the graphql-core execution adapter.

## 3. Hexagonal Architecture and Full Bridge

**Decision**: Domain owns self-enrollment ownership for trusted identities, duplicate-enrollment rules, course-offering eligibility and Enrollment invariants. Application owns identity-verification invocation/failure handling, Student/Programme/Course repository absence handling, exact FR-009 first-match sequencing and IdentityVerifier/EnrollmentUnitOfWork Protocol ports. Flask/Werkzeug/graphql-core objects, provider output and sqlite3 rows/exceptions are translated explicitly in adapters. Domain and Application are framework-free for this feature, without imposing a project-wide ban on Application frameworks.

**Rationale**: Explicit converters prevent external representations entering Core while allowing adapters to call supported Domain factories and controlled reconstitution APIs. Application uses Domain types directly where appropriate; no redundant internal DTO layer. Import Linter enforces inward import relationships and forbidden dependencies; architecture tests inspect public annotations/re-exports and demonstrate detection with violating fixtures. [Import Linter layers](https://import-linter.readthedocs.io/en/stable/contract_types/layers/).

**Alternatives considered**: Decorated Domain GraphQL types, raw transport dictionaries throughout Application or repository implementations making eligibility decisions would undermine isolation. Package naming and Protocols alone are not architecture enforcement. Dynamic imports, reflection and Any can bypass static inspection; forbid such escapes in Core and verify converter semantics behaviorally.

### Repository misses versus Domain policies

**Decision**: Application handles absent Student, Programme and Course repository results and returns Core-defined MissingStudent/MissingProgramme/MissingCourse rejection types. Do not route these through Domain functions merely wrapping None checks. Domain retains verified-identity ownership, duplicate-enrollment, offering-eligibility and Enrollment invariant decisions; Application sequences their invocation and returns their outcomes without re-evaluating their predicates.

**Rationale**: Handling unavailable repository results and dependent lookup prerequisites is use-case coordination. It does not require a Domain entity or an existence-policy abstraction. The Project Owner explicitly defines this responsibility split. It preserves Constitution I/II: Application coordinates required ports, Domain remains independent and owns actual policy. This is a feature design clarification, not a constitutional amendment or waiver.

**Contracts**: Application Core owns missing-record rejection types. Domain owns its policy reasons. The Application result union can include those Domain outcomes directly; Domain never imports Application. Repository absence is None, not an exception or malformed Domain object. Corrupt persisted data remains a technical adapter failure. Application's branching on Domain rejection/pass results is control flow, not permission to recompute actor equality, uniqueness or offering eligibility.

**Alternatives considered**: Trivial require_student/require_programme/require_course Domain guards add indirection without Domain behavior. Moving all decisions into Application would duplicate policies and violate the selected separation. Adapters selecting missing-record business outcomes would improperly own use-case flow. Keep the existing outward GraphQL reason names and all business semantics.

**Verification**: Application tests cover both present/absent repository results, exact first-match short circuits and unchanged state. Domain tests cover ownership for trusted identities, duplication, offering eligibility and construction/reconstitution/transitions. Combined-failure acceptance proves precedence across both owners, including already-enrolled plus ineligible -> ALREADY_ENROLLED without invoking eligibility. Coverage includes whole Application orchestration functions as well as all affected Domain policies; no reduction in coverage scope.

### Identity verification versus ownership

**Decision**: Application invokes its owned IdentityVerifier port, receives trusted VerifiedIdentity or None, and returns Core DENIED immediately on a negative result without ownership or persistence. Success supplies VerifiedIdentity and validated target StudentId to Domain ownership policy. Domain owns comparison/mismatch denial, not verification, and requires no verifier port or UnverifiedIdentity model. Application reuses the Core Denied value/type without Domain importing Application.

**Rationale**: The owner explicitly separates external identity verification from the self-enrollment ownership rule. Verification provenance comes from a trusted adapter; it does not establish Student existence. Application coordinates failure and precedence, while Domain receives valid identity values and owns the business predicate. Existing provider-unavailability technical outcomes remain distinct from negative verification and short-circuit equally early.

**Alternatives considered**: Passing a verification-result wrapper or UnverifiedIdentity into Domain unnecessarily couples policy to failed external verification. Letting Application compare actor and target duplicates Domain policy. Calling Domain for a negative result violates the requested short circuit. Domain calling a verifier port is not needed by this feature.

**Verification**: Application tests assert negative verification -> exact Core DENIED with zero ownership and persistence invocations; successful verification forwards actual trusted identity and StudentId. Domain tests cover matching/mismatched verified identity only. HTTP acceptance preserves identical generic denial and no disclosure; missing Student still has its distinct reason after verified matching identity. Architecture checks forbid Domain imports of Application verifier contracts; full-function coverage includes Application verification branches and Domain ownership branches.

## 4. Domain type safety and static quality

**Decision**: Distinct immutable value classes for StudentId, ProgrammeId, CourseId and SubjectId, using frozen dataclasses with explicit runtime validation. Normal creation follows shared `.create` APIs; persisted values/records use separate `.reconstitute` APIs. Entity factories accept validated Domain Types. Internal constructors preserve invariants but are not public alternatives. Tagged outcomes and exhaustive typed mapping preserve reason distinctions. Use strict mypy across source, Ruff lint/format, Import Linter and architecture/signature tests.

**Rationale**: [Python typing](https://docs.python.org/3.12/library/typing.html) documents that annotations are not runtime enforced and NewType does not wrap/validate runtime values. Frozen dataclasses do not deeply freeze nested collections. Validate actual value types and nonempty strings in Domain; keep immutable scalar fields/copies. [mypy](https://mypy.readthedocs.io/en/stable/command_line.html#cmdoption-mypy-strict) and [Ruff](https://docs.astral.sh/ruff/) supply separate static gates, not business guarantees.

**Alternatives considered**: Bare strings/aliases or NewType alone give insufficient runtime identity/invariant protection. Broad ignore_missing_imports, unchecked casts, Any and blanket suppressions would hide bridges. Limit unavoidable third-party typing gaps to adapter functions with runtime checks and explicit justifications. Pin checker versions and configuration; strict flags are not a promise to catch every dynamic defect.

## 5. Atomic save, eligibility and concurrent uniqueness

**Decision**: Embedded file-backed SQLite, one connection per operation, Python 3.12 `autocommit=True`, explicit SQL BEGIN IMMEDIATE before all prerequisite reads, explicit SQL COMMIT/ROLLBACK and connection close. Use a five-second lock timeout and composite student/course primary key. Application coordinates through the UoW port; SQL mechanics remain in the adapter.

**Rationale**: SQLite's one-writer behavior makes the prerequisite reads, Application absence handling, Domain policies and insertion one ordered save decision. A change committed before the transaction is read; a writer blocked behind enrollment changes state after enrollment commits. [SQLite transactions](https://www.sqlite.org/lang_transaction.html). Python connection commit()/rollback() do nothing in autocommit=True, so explicit SQL is necessary; defaults or autocommit=False do not establish the intended immediate scope. [Python transaction control](https://docs.python.org/3.12/library/sqlite3.html#transaction-control).

**Alternatives considered**: Check-then-save in separate transactions admits stale eligibility; process mutexes do not protect other processes; in-memory persistence cannot prove durability. SQLite serializes unrelated writers and limits write throughput; no multi-host/shared-filesystem or performance target is claimed. A database server is not necessary for the approved scope.

**Verification**: Real independent connections test duplicate races, save-time changes, rollback, lock failure and visibility after reopen. Keep identity-provider calls outside transactions. Classify unique-pair conflicts specifically; never map arbitrary integrity errors to duplicate rejection. Do not use INSERT OR REPLACE/IGNORE to hide rejection behavior. Never compensate/delete an enrollment after confirmed commit or response loss.

## 6. Outside-In TDD, coverage and evidence

**Decision**: Acceptance tests guide cohesive Outside-In Red/Green/Refactor increments. Use the existing deterministic identity double, real temporary SQLite and port spies. Tests MAY exercise several layers through a shared behavioral boundary. Retain lightweight commands/results associated with identifiable implementation states and execution order, distinguishing acceptance-first and inner TDD activity as specified in [plan.md](plan.md); evidence MAY be consolidated across cohesive increments. Refactoring consideration need not produce code changes or separate no-refactor artifacts. Import/configuration failures are not behavioral Red.

**Rationale**: Constitution v2.3.1 Principle III permits cohesive increments and consolidated evidence, and it does not require exhaustive per-behavior histories or intermediate snapshots. Final acceptance, regression, coverage, architecture, static analysis, and contract checks remain mandatory. Passing tests and coverage alone do not establish TDD.

**Alternatives considered**: Restoring the former prospective snapshot/per-behavior protocol as a mandatory gate would contradict the revised evidence rules. Discarding execution evidence and relying on final Green would also violate them. Keep richer historical records as optional support and migrate tooling to accept valid lightweight evidence. Preserve the recorded C1/T050 reconciliation under v2.0.0; reassess only claims dependent on the new evidence contracts, without manufacturing historical chronology.

**Coverage**: coverage.py branch measurement with a 100% combined statement-and-branch gate across the entire Domain and Application source directories, including unimported modules and all unchanged measurable branches. This stronger complete-scope gate implies all included functions' measurable branches are covered; it does not need a custom per-function coverage parser. Scope/exclusion/discovery audits and negative fixtures prevent vacuous passes. Any business behavior outside Core joins this scope. No business exclusions, no cover/no branch suppressions or changed-lines gate. Zero-branch functions still need behavioral tests. [Branch measurement](https://coverage.readthedocs.io/en/latest/branch.html), [configuration](https://coverage.readthedocs.io/en/latest/config.html).

**Alternatives considered**: A sub-100 complete-Core aggregate fails the approved project gate; constitutional compliance is assessed separately against 100% branches of each whole affected business-logic function/method. Changed-lines coverage cannot establish that floor, and a final green run alone cannot establish TDD. Coverage is not proof of complete scenarios; exception, construction, reconstitution, transition, privacy and concurrency tests remain necessary. Generated code/configuration does not authorize hiding business behavior.

## Resolution

Feature decisions for ports, factories, integrity, evidence, and fitness are recorded in [plan.md](plan.md). Python is selected by explicit owner requirement. The Student detail extension below adds the specified behavior within the current feature. No constitutional waiver, additional service, or production implementation is introduced by this research. Runtime dependencies and test gates are planned, not executed by this documentation workflow.


## 7. Required Student text and case-insensitive email (extension)

**Decision**: Add immutable StudentName and StudentEmail values; reject non-string, empty and whitespace-only input using Python whitespace semantics, without mutating supplied text. Student requires both values at construction and restoration. Compare the full email using str.casefold(), preserving the original value separately.

**Rationale**: Local text validity belongs to Domain and must survive direct constructor calls and persistence adaptation. Casefold supports Unicode caseless matching, including expansions; lower() or SQLite NOCASE would not implement the same semantics for unrestricted text. See [Python string methods](https://docs.python.org/3.12/library/stdtypes.html#str.casefold) and [SQLite collations](https://www.sqlite.org/datatype3.html#collating_sequences). Domain defines a pure email-availability policy taking candidate owner and any conflicting owner; Application coordinates lookup, avoiding Domain dependencies on infrastructure.

**Alternatives considered**: Bare strings spread validation; annotations alone do not enforce runtime invariants. Trimming, syntax validation, Unicode composition normalization and provider alias matching introduce unrequested rules. ASCII-only matching silently narrows unrestricted text.

## 8. Atomic global uniqueness and persistence

**Decision**: Keep SQLite and current runtime dependencies. Register deterministic functions backed by Domain text validation/comparison on every adapter-managed connection. Add nonblank name/email constraints and a unique expression index students_email_key on the casefold function result. Use one immediate transaction for owner lookup, Domain decision and create/replace. Only the email index's unique failure translates to EmailConflict; rollback preserves old values and existing enrollments.

**Rationale**: A database index arbitrates concurrent claims and protects direct writes on configured connections. A function-derived expression index cannot contain a forged independent email key. Python exposes deterministic connection-local SQL functions: [sqlite3 create_function](https://docs.python.org/3.12/library/sqlite3.html#sqlite3.Connection.create_function). The connection factory must register functions before use; unconfigured writers fail rather than silently applying different rules. Freeze the Python 3.12 comparison contract; future Unicode/runtime changes require index compatibility review and rebuild before upgrade.

**Alternatives considered**: A preflight lookup alone races. A process lock misses other processes. NOCASE is ASCII limited. A writable normalized column can drift unless constrained. A custom collation is viable but still requires per-connection registration; deterministic functions additionally reuse the nonblank predicate. No new database/server or ICU dependency is needed.

## 9. Integration boundary, compatibility and proof

**Decision**: Expose a small internal Python Application operation for host student-record create/replace, with a separate UoW port and typed results documented in contracts/student-details.md. Keep GraphQL SDL unchanged. User Story 2 acceptance calls this integration boundary using real SQLite; User Story 1 continues through Flask HTTP. Existing legacy schema is detected and refused without automatic migration or invented values.

**Rationale**: The new scenarios need an observable transactional operation, while the specification excludes a management interface. A host-only Python integration contract exercises orchestration and persistence without adding a web product flow. Global uniqueness cannot be established by a standalone Student constructor. Domain construction still enforces all locally decidable invariants; contextual uniqueness is checked by Domain policy plus atomic persistence.

**Alternatives considered**: New GraphQL mutations or CLI management commands expand scope; testing only Student constructors cannot prove concurrency or persistence; direct SQL acceptance alone would bypass the Core policy and integration results. Nullable/default names/emails would weaken required attributes. Automatic legacy backfill cannot derive real values.

**Evidence impact**: The current inventory already includes all 15 enrollment identities and 23 parameterized Student cases across seven scenario families. Preserve it. Extend state/chronology verification as described below; historical passes do not validate the new contracts.

## 10. Expected failure contracts

**Decision**: Use Domain result-returning validation factories, existing typed policy
rejections, repository absence values, and explicit PairConflict/EmailKeyConflict
port results. Preserve deterministic first-match input/business validation. Retain
Core-owned technical exceptions solely for documented operational faults; propagate
programming/internal-contract defects to the outer error boundary.

**Rationale**: Local source inspection found constructor ValueError catches and a
raised UniqueConflict retry path in application/enroll.py, plus a blanket Exception
catch in adapters/identity/verifier.py. Those paths are migration targets under the
new constitution, not evidence of alignment. Factories keep rules in Domain while
Application coordinates invalid raw input without exceptions. Precise constraint
translation hides driver types without treating unrelated faults as conflicts.

**Alternatives considered**: Constructor exceptions caught as validation violate the
new rule; duplicated Application predicates weaken Domain ownership. Making every
technical exception a business rejection conceals defects. An all-result technical
port design is possible but unnecessary: the constitution permits technical exceptions
when explicitly contracted and translated separately. Accumulating independent text
errors is optional; the current name-before-email rule is retained.

**Verification**: Add fresh behavioral evidence for returned invalid-ID/text results,
returned conflict/replay outcomes, provider-outage versus negative verification,
corrupt-row technical classification and programming-error propagation. Validate
no infrastructure exceptions appear in Core signatures or outcomes. This is a local
contract amendment; no new dependency or external API choice is introduced.

## 11. StudentEmail equality, hashing and Student identity

**Decision**: Define StudentEmail equality over its complete Unicode `str.casefold()`
key and derive its hash from that same immutable key. Compare only StudentEmail
instances; return NotImplemented for other types. Preserve submitted text independently.
Student identity/equality uses StudentId alone, with a matching ID-based hash if
hashable.

**Rationale**: The owner explicitly requires value equality to agree with whole-address
caseless uniqueness. Original-case dataclass equality/hash would disagree with that
rule. A consistent hash makes equal values interchangeable in sets/dictionaries.
Email is replaceable and cannot define Student identity. No new technology research
or dependency choice is required for this local Domain design decision.

**Alternatives considered**: Original-text equality contradicts the requested semantics;
lower(), partial-address matching and provider normalization alter the specified key.
String coercion would introduce heterogeneous equality. Email-based Student identity
would change identity on replacement and confuse uniqueness with entity identity.
Persisted Python hashes are unsuitable; persistence continues using the comparison key.

## 12. Source-inspected evidence compatibility (2026-10-22)

**Decision**: Apply the evidence rules in [plan.md](plan.md), retaining current lightweight capture and final-digest
verification while implementing state and activity association. The recorder already
accepts lowercase `red`, `green`, `refactor` and `verification`; no EVIDENCE_REQUEST,
snapshots, global hash chain, per-behavior approvals or no-refactor records are required.

**Rationale**: `scripts/record.py:capture` writes commands, output, result and execution
times but does not call its existing digest function or capture revision/state identity.
`scripts/check_evidence.py:validate_runs` recognizes AssertionError Red followed by
successful Green and checks group/time order, but not state association, test correspondence
or acceptance/inner roles. Missing times may default to zero. `check_quality.py` and
assembly/validation protect final-state freshness; they do not prove historical chronology.

**Alternatives considered**: Final Green alone, timestamps alone or bare differing
hashes cannot prove test-first development. A mandatory commit or source snapshot for
every cycle adds an unrequested mechanism. Shared D4 instead requires reviewable state
references, actual ordering and ordinary review of the behavior implemented between runs.
Preserve historical bytes and report missing associations rather than invent metadata.

**Verification**: Positive consolidated/shared-suite evidence and negative absent state,
unrelated tests, missing role/context, invalid chronology and stale final results. Update
fixtures that currently accept output/time-only records. New behavioral validation follows
TDD; historical behavior already passing needs no manufactured Red.

## 13. Structural and semantic verification responsibilities

**Decision**: Apply the port and fitness rules in [plan.md](plan.md) and preserve configured quality/coverage gates. Import
Linter is the primary static dependency checker. Targeted architecture tests cover
public annotations and dynamic imports; the new gap is model factory/caller coverage.
Semantic conversions, data-integrity classification, business decisions and short circuits
are verified by behavioral contracts and explicit semantic review, separately identified.

**Rationale**: Current `tests/architecture/test_boundaries.py` already removed obsolete
exact policy-call/source-comparison constraints. Do not schedule that completed cleanup
again. Import graphs and public annotations cannot establish what arbitrary container
contents mean. Passing dependencies must not be called semantic boundary proof.

**Alternatives considered**: A second general import graph duplicates protection;
removing semantic tests loses it. Absolute constructor privacy is neither required nor
assumed. Use allowed/violating caller fixtures and behavioral factory/restoration tests.
The complete-Core 100% statement-and-branch gate remains stricter than the constitutional
whole-affected-function branch minimum; no exclusion, scope or target relaxation occurs.

## 14. Uniform construction and data-integrity contracts

**Decision**: [plan.md](plan.md) defines `.create` and `.reconstitute` and Domain
InvalidPersistedState -> Core DataIntegrityFailure(StorageFailure) -> existing sanitized
public technical outcome. Feature signatures and per-model invariants are in
[domain-construction.md](contracts/domain-construction.md).

**Rationale**: Source inspection found raw-input Student/Enrollment `.create` methods,
missing Programme/Course/ProgrammeCourseOffering/VerifiedIdentity factories, normal
Enrollment and verified-identity direct constructor calls, and constructor-based row
loaders with no explicit restoration APIs. `decode` already identifies invalid stored
values as generic StorageFailure; retain technical handling and add identifiable
integrity classification, not new business rejection reasons.

**Alternatives considered**: Keeping validating constructors public contradicts the
requested API style even for entities with no extra invariants. Entity factories that
parse untrusted scalars bypass the validated-Domain-Type input contract. Reapplying
current offering or email-availability eligibility while restoring creates false
historical rejections. Mapping corruption to INVALID_REQUEST or missing records
confuses saved-state integrity with caller input. No new enrollment rule, schema change,
management endpoint, dependency or language-level privacy mechanism is needed.

## 15. Constitution v2.3.1 reassessment

**Decision**: Treat Constitution v2.3.1 as the binding policy for this feature.
Record ports, factories, reconstitution, evidence, and fitness in [plan.md](plan.md).
Do not add `.specify/memory/architecture-decisions.md`. Keep the selected stack:
Python 3.12, Flask, graphql-core 3.3, Waitress, file SQLite, pytest, strict mypy,
Ruff, Import Linter, and coverage.py at 100% statement and branch coverage over
the whole Domain and Application source trees.

**Rationale**: The constitution file is version 2.3.1, effective 2026-10-22, and
the specification says this feature complies with it without changing enrollment
eligibility, FR-009, or student-detail validity. Source inspection on 2026-10-22
confirms the migration described in sections 12–14 is still open: entity factories
still parse raw scalars, several models have no factory, reconstitution and
`InvalidPersistedState` are absent, `enroll` constructs `Enrollment` directly,
SQLite decode uses `.create` and raises a generic storage failure, and
`scripts/record.py` stores output and times without the implementation digest or
an acceptance-versus-inner role. `digest()` already exists and is unused by
capture. Those are implementation gaps, not unresolved design questions.

User Story 2 scenarios 8–10 and FR-014 are specified. Application tests cover
existing-student create, missing-student replace, and empty identifiers.
`scripts/acceptance_inventory.py` still requires exactly the original twenty-three
Student cases, and HTTP acceptance does not yet identify FR-014. The plan adds
those identities without a new GraphQL reason or eligibility rule.

**Alternatives considered**: Leaving the plan on “proposed v2.1.0” contradicts the
ratified constitution. Recreating a shared decisions file would duplicate the
constitution and the feature plan. Treating historical C1/T050 evidence as v2.3.1
proof would invent chronology the records do not contain.

**Resolution**: No technical clarification remains open. Implementation, evidence
migration, and final-state checks remain pending. This research does not certify
implementation compliance.
