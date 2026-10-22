# SDD-DDD-TDD Codex Constitution

## Core Principles

### I. Hexagonal Architecture and Inward Dependencies

The system MUST follow Hexagonal Architecture. Its Core MUST contain Application
(outer Core, responsible for use-case orchestration) and Domain (inner Core,
responsible for business decisions, models, state transitions, and invariants).
Clean Architecture dependency rules MUST apply within this Core:

- Application MAY depend on Domain.
- Infrastructure and Transport Adapters MAY depend on Application and/or Domain.
- Domain MUST NOT depend on Application, Infrastructure, or Transport.
- Application MUST NOT depend on concrete Infrastructure or Transport Adapters.
- Core operations needing external capabilities MUST use Core-owned Ports.

Inbound Adapters MUST handle external interaction, translate boundary representations,
and delegate application use cases to Application. Outbound Adapters MUST implement
Core-owned Ports and handle technical integration with external systems.

Adapters MAY directly use public Domain types, constructors, factories, and other
public Domain mechanisms where necessary for technical boundary adaptation, provided
Domain invariants and dependency constraints are preserved. Application MUST NOT be
a mandatory gateway for such technical boundary adaptation. Direct Domain access
MUST NOT be interpreted as permission for Adapters to orchestrate complete application
use cases.
Domain MUST remain independent of application frameworks, persistence frameworks,
transport technologies, and external service SDKs. Application MAY use libraries
and frameworks for application responsibilities, provided dependency direction
and Domain ownership of business decisions remain intact.

These rules isolate business policy from external technologies without requiring
redundant mappings solely to satisfy layering.

### II. Domain Ownership, Integrity, and Boundary Contracts

Business decisions, business rules, state transitions, and invariants MUST reside
in Domain. Application MUST own use-case orchestration and coordination of Domain
operations and required Ports without duplicating or overriding Domain decisions.
Adapters MUST NOT implement Domain business decisions or assume responsibility for
application use-case orchestration.
Business requirements MUST drive modeling rather than persistence or transport
representations.

Entities and value objects MUST preserve invariants during construction,
reconstitution, and transitions, regardless of caller. Domain MUST NOT rely on
external validation for invariant enforcement. Application MAY hold invalid,
incomplete, or unvalidated input and intermediate state, but MUST NOT represent
such state as valid Domain objects.

Predictable input validation failures and business rejections MUST be represented
through explicit failure results rather than exceptions used for normal control flow.
Domain MUST define and enforce its own invariants. Application MUST coordinate
validation of untrusted input and MAY accumulate independent validation errors before
invoking operations that require valid Domain values.

Exceptions MAY be used for unexpected technical failures, programming errors, and
violations of internal contracts. Such exceptions MUST NOT be silently converted
into business rejections.

Boundary contracts MUST distinguish expected failures from unexpected failures and
define how each is propagated or translated. Infrastructure-specific exception types
MUST NOT leak into Domain or Application contracts. These rules make expected
outcomes explicit while preserving visibility of unexpected failures.

Full Bridge boundary isolation MUST use explicit contracts and conversions wherever
representations differ and MUST prevent external Infrastructure and Transport
representations from leaking into Core. Conversions into Domain MUST preserve
invariants. Application MAY use Domain types internally. Full Bridge boundary
isolation MUST NOT require redundant DTOs or mappings solely to separate Application
from Domain; redundant wrappers and mappings MUST NOT be required solely for
architectural layering.

### III. Outside-In Test-Driven Development

All new or modified business behavior MUST use Outside-In TDD. Feature development
MUST begin with executable acceptance tests. Acceptance tests MUST express business
outcomes derived from the approved specification at a declared public boundary.
Acceptance tests MUST guide subsequent inner-layer TDD cycles until the specified
outcomes are satisfied. Writing an acceptance test first MUST NOT, by itself, be
considered sufficient evidence of Outside-In TDD. Each independently testable
behavior increment MUST still follow Red → Green → Refactor as defined below.

Planning MUST declare the public acceptance-test boundary and select any transport
protocol, acceptance-test framework, test-double strategy, and test environment.
This Constitution MUST NOT mandate a specific choice for any of those technologies
or strategies.

Each affected layer, including Application, Domain, and Adapters, MUST have its
responsibilities verified by appropriate automated tests. Production behavior in
each affected layer MUST be driven by failing tests.

Every independently testable behavior increment MUST follow Red → Green → Refactor:

- Red: write and execute a test that fails for the expected behavioral reason before
  implementing the corresponding production behavior. Infrastructure, configuration,
  or unrelated failures alone MUST NOT count as Red.
- Green: implement the minimum production code necessary to pass the test.
- Refactor: improve design where appropriate while preserving behavior, then rerun
  relevant tests.

Test scope and granularity MUST reflect layer responsibilities and risks. Tests MUST
verify observable behavior and architectural responsibilities, rather than
implementation details. Separate test files or classes MUST NOT be required solely
to mirror production structure.

Tests MUST NOT be weakened, deleted, skipped, or modified solely to make an
implementation pass. Changes to existing tests MUST be justified by approved
requirement changes or verified test defects.

TDD compliance MUST have recorded execution evidence showing commands, results,
execution order, and relevant failures for Red → Green → Refactor. Agent summaries
without corresponding execution evidence MUST NOT satisfy this requirement.

### IV. Automated Architecture and Coverage Verification

Automated architecture fitness tests MUST enforce dependency direction, Core
independence, Domain isolation from external frameworks and Adapters, and boundary
contract and type isolation. Violations MUST fail the relevant checks. Automated
behavioral tests MUST verify Domain invariants during construction, reconstitution,
and state transitions where applicable.

Every new or modified business-logic function or method MUST achieve 100% branch
coverage, measured by automated tooling. The minimum coverage measurement unit MUST
be the entire affected function or method, including its unchanged measurable
branches, rather than only newly introduced or modified branches. Applicable Domain
and Application business logic MUST be included.

Functions or methods with no measurable branches MUST still satisfy applicable
behavioral testing requirements. Branch coverage alone MUST NOT be treated as
sufficient verification or as proof of behavioral correctness or complete business
scenario coverage.

Planning MUST identify the applicable coverage scope, tooling, and justified
exclusions, but MUST NOT weaken the constitutional minimum. Coverage exclusions MUST
be explicitly justified and MUST NOT conceal untested business behavior.

### V. Evidence-Based Completion

Before declaring a feature complete, all applicable mandatory checks MUST run
against the final implementation state, pass, and have their required evidence
available. Failed, skipped, blocked, or unexecuted mandatory checks MUST be reported.
Agents MUST NOT claim completion from self-assessment, incomplete verification,
or results that do not match the final implementation state.

The project MUST define and enforce automated static quality checks. Planning MUST
establish the applicable tools, rules, and configurations.

## Architecture Decisions and Open Questions

The following items identify ambiguity in the source draft. They do not authorize
exceptions to the explicit principles above. Feature plans MUST resolve applicable
items before implementing behavior that depends on them; unresolved items MUST be
reported rather than silently assigned a project-wide interpretation.

- TODO(ARCHITECTURE_BOUNDARIES): During feature planning, identify the boundary
  contracts and conversions required where external and Core representations differ,
  and define transaction-coordination details consistent with Application ownership
  of use-case orchestration. These choices MUST preserve direct Domain access for
  technical boundary adaptation without assigning use-case orchestration to Adapters
  or requiring redundant Application-to-Domain DTOs or mappings.
- TODO(PORT_OWNERSHIP): Define when a Port belongs to Domain versus Application,
  how cross-context communication works, and where transaction boundaries reside.
  No bounded contexts, aggregate boundaries, or deployment topology are specified;
  Hexagonal Architecture alone does not select a monolith or microservices.
- TODO(APPLICATION_FRAMEWORKS): Define which Application framework dependencies are
  acceptable, including framework-owned types in public contracts. Clarify whether
  “Core independence” in fitness tests means dependency direction or framework freedom,
  since Application explicitly permits frameworks.
- TODO(FITNESS_TEST_SCOPE): Select enforceable module boundaries and fitness-test
  tooling. Distinguish statically testable dependencies from semantic representation
  leakage requiring behavioral tests or review.
- TODO(TDD_SCOPE): Define treatment of behavior-preserving refactors, generated code,
  configuration, and exploratory work. Clarify whether layer-specific failing tests
  must be separate tests or may be satisfied by broader behavioral tests.
- TODO(ACCEPTANCE_TEST_BOUNDARY): During feature planning, declare the public boundary
  at which acceptance tests express specified business outcomes, and select any
  transport protocol, acceptance-test framework, test-double strategy, and test
  environment. Specification approval authority remains to be identified. The
  acceptance-guided relationship to inner TDD cycles is defined in Principle III
  and is not an unresolved planning choice.
- TODO(TDD_EVIDENCE): Define evidence location, retention, association with code
  revisions, and review mechanism. Specify what evidence is required when no refactor
  is needed and how later edits invalidate prior verification.
- TODO(COVERAGE_SCOPE): During feature planning, identify all applicable new or
  modified business-logic functions and methods, including Domain and Application
  logic; select tooling and map changes to entire affected functions or methods.
  Document justified exclusions and identify their approval authority. Planning
  decisions MUST NOT weaken the whole-function-or-method minimum in Principle IV
  or use exclusions to conceal untested business behavior.

## Development Workflow and Quality Gates

1. Specifications MUST state the business behavior used to derive acceptance tests.
2. Plans MUST identify responsibilities across Domain, Application, Ports, and Adapters;
   define applicable coverage scope and static checks; and resolve applicable open
   questions above.
3. Tasks and implementation MUST preserve test-first ordering and record execution
   evidence for each behavior increment.
4. Completion review MUST inspect architecture checks, invariant and acceptance tests,
   coverage, static checks, and TDD evidence against the final implementation state.
   Any missing or failing mandatory check prevents a successful completion claim.

## Governance

This constitution governs feature specifications, plans, tasks, and implementation.
Those artifacts MUST comply with its effective requirements. The source draft is
reference material; unresolved questions above MUST NOT be treated as settled policy.

Amendments MUST document the proposed text, rationale, compatibility impact, and
migration requirements, and receive explicit project-owner approval before being
represented as ratified policy. The Project Owner is the constitutional approval
authority.

Versions MUST use semantic versioning: MAJOR for incompatible principle removals or
redefinitions; MINOR for new principles or materially expanded guidance; PATCH for
non-semantic clarifications and corrections. Every amendment MUST update its version
and amendment date and record its impact for review. Specifications, plans, and
completion reviews MUST assess compliance and explicitly report deviations; a plan
alone MUST NOT waive a mandatory constitutional rule.

**Version**: 1.4.0 | **Ratified**: 2026-10-21 | **Last Amended**: 2026-10-21
