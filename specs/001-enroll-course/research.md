# Research: Python 3.12 Student Self-Enrollment

**Date**: 2026-10-21 | **Spec**: [spec.md](spec.md) | **Constitution**: v2.0.0

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

**Rationale**: Explicit converters prevent external representations entering Core while allowing adapters to call public validating Domain constructors. Application uses Domain types directly where appropriate; no redundant internal DTO layer. Import Linter enforces inward import relationships and forbidden dependencies; architecture tests inspect public annotations/re-exports and demonstrate detection with violating fixtures. [Import Linter layers](https://import-linter.readthedocs.io/en/stable/contract_types/layers/).

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

**Decision**: Distinct immutable value classes for StudentId, ProgrammeId, CourseId and SubjectId, using frozen dataclasses with explicit runtime validation. Plain Domain entities preserve invariants on construction, reconstitution and transitions. Tagged outcomes and exhaustive typed mapping preserve reason distinctions. Use strict mypy across source, Ruff lint/format, Import Linter and architecture/signature tests.

**Rationale**: [Python typing](https://docs.python.org/3.12/library/typing.html) documents that annotations are not runtime enforced and NewType does not wrap/validate runtime values. Frozen dataclasses do not deeply freeze nested collections. Validate actual value types and nonempty strings in Domain; keep immutable scalar fields/copies. [mypy](https://mypy.readthedocs.io/en/stable/command_line.html#cmdoption-mypy-strict) and [Ruff](https://docs.astral.sh/ruff/) supply separate static gates, not business guarantees.

**Alternatives considered**: Bare strings/aliases or NewType alone give insufficient runtime identity/invariant protection. Broad ignore_missing_imports, unchecked casts, Any and blanket suppressions would hide bridges. Limit unavoidable third-party typing gaps to adapter functions with runtime checks and explicit justifications. Pin checker versions and configuration; strict flags are not a promise to catch every dynamic defect.

## 5. Atomic save, eligibility and concurrent uniqueness

**Decision**: Embedded file-backed SQLite, one connection per operation, Python 3.12 `autocommit=True`, explicit SQL BEGIN IMMEDIATE before all prerequisite reads, explicit SQL COMMIT/ROLLBACK and connection close. Use a five-second lock timeout and composite student/course primary key. Application coordinates through the UoW port; SQL mechanics remain in the adapter.

**Rationale**: SQLite's one-writer behavior makes the prerequisite reads, Application absence handling, Domain policies and insertion one ordered save decision. A change committed before the transaction is read; a writer blocked behind enrollment changes state after enrollment commits. [SQLite transactions](https://www.sqlite.org/lang_transaction.html). Python connection commit()/rollback() do nothing in autocommit=True, so explicit SQL is necessary; defaults or autocommit=False do not establish the intended immediate scope. [Python transaction control](https://docs.python.org/3.12/library/sqlite3.html#transaction-control).

**Alternatives considered**: Check-then-save in separate transactions admits stale eligibility; process mutexes do not protect other processes; in-memory persistence cannot prove durability. SQLite serializes unrelated writers and limits write throughput; no multi-host/shared-filesystem or performance target is claimed. A database server is not necessary for the approved scope.

**Verification**: Real independent connections test duplicate races, save-time changes, rollback, lock failure and visibility after reopen. Keep identity-provider calls outside transactions. Classify unique-pair conflicts specifically; never map arbitrary integrity errors to duplicate rejection. Do not use INSERT OR REPLACE/IGNORE to hide rejection behavior. Never compensate/delete an enrollment after confirmed commit or response loss.

## 6. Outside-In TDD, coverage and evidence

**Decision**: Acceptance tests guide cohesive Outside-In Red/Green/Refactor increments. Use the existing deterministic identity double, real temporary SQLite and port spies. Tests MAY exercise several layers through a shared behavioral boundary. Retain lightweight commands/results demonstrating relevant behavioral failure before implementation and passing tests afterward; evidence MAY be consolidated across cohesive increments. Refactoring consideration need not produce code changes or separate no-refactor artifacts. Import/configuration failures are not behavioral Red.

**Rationale**: Constitution v2.0.0 explicitly permits coherent grouping and rejects exhaustive per-behavior histories and intermediate snapshots as mandatory proof. Final acceptance/regression, coverage, architecture, static analysis and contract checks remain mandatory. Passing tests and coverage alone do not establish TDD.

**Alternatives considered**: Retaining the current prospective snapshot/per-behavior protocol as a mandatory gate would contradict the revised evidence rules. Discarding execution evidence and relying on final Green would also violate them. Keep richer historical records as optional support and migrate tooling to accept valid lightweight evidence. Reassess C1 from original execution records without treating grouping alone as a violation or declaring the finding automatically resolved.

**Coverage**: coverage.py branch measurement with a 100% combined statement-and-branch gate across the entire Domain and Application source directories, including unimported modules and all unchanged measurable branches. This stronger complete-scope gate implies all included functions' measurable branches are covered; it does not need a custom per-function coverage parser. Scope/exclusion/discovery audits and negative fixtures prevent vacuous passes. Any business behavior outside Core joins this scope. No business exclusions, no cover/no branch suppressions or changed-lines gate. Zero-branch functions still need behavioral tests. [Branch measurement](https://coverage.readthedocs.io/en/latest/branch.html), [configuration](https://coverage.readthedocs.io/en/latest/config.html).

**Alternatives considered**: A sub-100 complete-Core aggregate fails the approved project gate; constitutional compliance is assessed separately against 100% branches of each whole affected business-logic function/method. Changed-lines coverage cannot establish that floor, and a final green run alone cannot establish TDD. Coverage is not proof of complete scenarios; exception, construction, reconstitution, transition, privacy and concurrency tests remain necessary. Generated code/configuration does not authorize hiding business behavior.

## Resolution

All applicable planning questions have decisions in [plan.md](plan.md). Python is selected by explicit owner requirement, not as a provisional alternative. The Student detail extension below adds the newly specified behavior within the current feature; no constitutional waiver, additional service or production implementation is introduced. Runtime dependencies and test gates are planned, not executed by this documentation workflow.


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

**Evidence impact**: Existing scripts count only 15 enrollment scenarios and fixed historical increments. Extend manifest assembly/validation and negative fixtures to require all seven additional named scenario families and new increment evidence; historical passes do not validate the new spec. No unresolved research question or constitutional exception remains.

## 10. Expected failure contracts (v2.0.0 amendment)

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

## 12. Constitution v2.0.0 tooling compatibility

**Decision**: Schedule recorder, manifest/validator and negative-fixture alignment in
subsequent tasks. Current working-tree scripts enforce snapshots, per-behavior mappings
and REFACTOR/NO_REFACTOR records; the earlier positional CLI examples are obsolete.
The current recorder requires EVIDENCE_REQUEST JSON and uppercase stages; no
compatible lightweight CLI is claimed until migration is implemented. Keep final
source/check digest freshness separate from optional intermediate snapshots.

**Rationale**: Documentation alignment cannot establish that the existing gates accept
consolidated cohesive increments. Historical review and new work need honest execution
evidence, while final-state verification remains unchanged.

**Alternatives considered**: Recreating historical failures or automatically flipping
review status would manufacture proof. Leaving obsolete gate requirements mandatory
would defeat the amendment. No external research or dependency change is needed for
this policy migration; the constitution and local source are the decision bases.

## 13. Remove process-only mechanisms; simplify distinct verification responsibilities

The plan consolidates these decisions into one verification design. Required acceptance
scenario identities remain independent from the flexible grouping of TDD evidence;
no fixed inventory of future increment IDs is a completion requirement.

**Decision**: Replace prospective snapshots/blobs, global hash-chain continuity,
per-behavior maps/reviews and compulsory refactor/no-refactor stages with consolidated
lightweight commands/results and ordinary review context. Preserve historical files
and final-check digest integrity. The current fixed historical increment inventories
are not a valid mandatory organization for future cohesive increments.

**Rationale**: These process mechanisms exist to enforce the superseded granularity.
Actual behavioral failures before implementation and passes afterward remain required;
a complex protocol does not add constitutional obligations. Keep final quality results
and required acceptance identities independent from TDD log layout.

**Decision**: Make Import Linter the primary dependency graph verifier. Consolidate
redundant AST import rules after equivalent positive/negative fixture coverage is
shown. Retain targeted public-type/dynamic-escape checks and semantic converter tests.
Replace exact call-name sets and source-text ownership checks with meaningful
behavioral ownership and short-circuit tests.

**Rationale**: Local inspection of `tests/architecture/test_boundaries.py` shows import
checks overlap configured Import Linter rules, while annotations, dynamic loading
and boundary semantics require distinct verification. Exact `policies` call sets and
comparison substrings constrain implementation spelling rather than responsibility.

**Alternatives considered**: Deleting all fitness tests in favor of imports alone
would lose boundary semantics/type protection. Keeping two general import scanners
adds maintenance without a distinct responsibility. Retain specialized checks only
where they close a demonstrated gap, and preserve every approved architecture rule.

**Coverage decision**: Constitution IV sets whole-affected-business-function 100%
branch coverage. The configured complete-Core 100% statement-and-branch target is a
stronger approved project policy and remains unchanged. No exclusion, scope or target
relaxation is authorized by this planning update. No new dependency decision or
external research is needed; the constitution, source and configuration are the bases.
