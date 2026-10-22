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

Adapters MAY parse and validate external representations and convert them into Domain
Types using supported Domain factories when performing technical boundary adaptation.
They MAY directly use supported Domain factory APIs, controlled reconstitution APIs,
and other public Domain mechanisms,
provided the construction contracts in Principle II and dependency constraints
are preserved. Application MUST NOT be a mandatory gateway for such technical boundary
adaptation. Direct Domain access MUST NOT be interpreted as permission for Adapters
to orchestrate complete application use cases. Validation performed by Adapters MUST
NOT duplicate or replace Domain business rules. Validation MUST NOT be duplicated
solely to satisfy architectural layering.
Domain MUST remain independent of application frameworks, persistence frameworks,
transport technologies, and external service SDKs. Application MAY use libraries
and frameworks for application responsibilities, provided dependency direction
and Domain ownership of business decisions remain intact.

These rules isolate business policy from external technologies without requiring
redundant mappings solely to satisfy layering.

### II. Domain Ownership, Integrity, and Boundary Contracts

Business decisions, business rules, state transitions, and invariants MUST reside
in Domain. Application MUST coordinate use-case-level validation, authorization,
and business orchestration through Domain operations and required Ports, without
duplicating or overriding Domain decisions. Domain MUST remain the authoritative
owner of Domain invariants and the exclusive owner of business decisions.
Adapters MUST NOT implement Domain business decisions or assume responsibility for
application use-case orchestration.
Business requirements MUST drive modeling rather than persistence or transport
representations.

**Domain Construction Contracts**

Factory-based normal creation is a project-wide architectural API style for both
Value Objects and Entities, independently of their current validation complexity.

- All Value Objects and Entities MUST expose consistent, explicit factory APIs for
  normal creation and MUST enforce their invariants regardless of caller. Domain
  MUST NOT rely on external validation for invariant enforcement.
- Expected validation and business creation failures MUST return explicit outcomes.
  Expected invalid input to a supported factory MUST NOT be reclassified as an
  internal contract violation.
- Direct constructors MAY exist as internal implementation mechanisms but MUST NOT
  be supported as alternative public creation APIs, even when they validate inputs.
  Internal constructor misuse MAY raise exceptions as an internal contract violation.
- Language-level absolute constructor privacy MUST NOT be required. Language-specific
  mechanisms MAY vary; appropriate automated checks MUST enforce the supported API
  contract. Constructor accessibility alone does not make a constructor a supported
  public creation API.
- Entity factories MUST accept validated Domain Types and enforce all applicable
  entity-level invariants, including any cross-field constraints, regardless of
  whether additional cross-field constraints currently exist. Validated Domain Types
  are Domain-owned types whose applicable invariants have been enforced through their
  own controlled APIs; their use does not replace entity-level validation.

**Reconstitution**

Normal creation admits a new Domain object under current creation rules. Persistence
reconstitution restores previously persisted Domain state under its own contract.

- Reconstitution MUST be an allowed, controlled Domain API separate from normal
  creation factories. It MUST NOT be classified as a prohibited alternative public
  creation API.
- Reconstitution MUST enforce persisted-state invariants without reapplying
  creation-only eligibility rules. A persisted-state invariant is a rule that restored
  state must satisfy to be valid; creation-only eligibility governs admission of new
  objects and need not remain true afterward.
- Invalid persisted state MUST be classified as a data-integrity failure, not as
  user-input validation failure or ordinary business rejection. The shared error
  contract MAY establish its concrete representation and propagation mechanism.
- Persistence Adapters MAY invoke reconstitution directly when implementing
  Core-owned Ports. Application MUST NOT be a mandatory gateway for this adaptation.

Entities and Value Objects MUST also preserve applicable invariants during state
transitions. Application MAY hold invalid, incomplete, or unvalidated input and
intermediate state, but MUST NOT represent such state as valid Domain objects.
These contracts keep validation outcomes explicit and normal-creation APIs consistent,
while allowing valid historical state to be restored after eligibility has changed.

Predictable input validation failures and business rejections MUST be represented
through explicit Result-style outcomes rather than exceptions used for normal control
flow.
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

New or changed business behavior MUST follow Outside-In TDD using cohesive
behavioral increments. Feature development MUST begin with executable acceptance
tests. Acceptance tests MUST express business outcomes derived from the approved
specification at a declared public boundary.
Acceptance tests MUST guide subsequent inner-layer TDD cycles until the specified
outcomes are satisfied. Writing an acceptance test first MUST NOT, by itself, be
considered sufficient evidence of Outside-In TDD. Each cohesive behavioral increment
MUST still follow Red → Green → Refactor as defined below.

Planning MUST apply project-wide testing policies, declare the public acceptance-test
boundary, and select feature-specific transport protocols, acceptance-test frameworks,
test-double strategies, and test environments where project policy leaves choices open.
This Constitution MUST NOT mandate a specific choice for any of those technologies
or strategies.

Each affected layer, including Application, Domain, and Adapters, MUST have its
responsibilities verified by appropriate automated tests. Tests MAY exercise multiple
layers through a shared behavioral boundary.

Each increment MUST:

1. Execute a relevant failing behavioral test before implementing the behavior (Red).
   The test MUST fail for the expected behavioral reason; infrastructure,
   configuration, or unrelated failures alone MUST NOT count as Red.
2. Implement the behavior required by the increment and verify that the relevant
   tests pass (Green).
3. Consider refactoring and verify that relevant tests remain passing (Refactor).

Related behaviors MAY be grouped into one increment when they form a coherent
implementation unit. Separate cycles for every assertion, branch, or independently
testable behavior are NOT required.

Refactoring does not require code changes when none are warranted.

Test scope and granularity MUST reflect layer responsibilities and risks. Tests MUST
verify observable behavior and architectural responsibilities, rather than
implementation details. Separate test files or classes MUST NOT be required solely
to mirror production structure.

Tests MUST NOT be weakened, deleted, skipped, or modified solely to make an
implementation pass. Changes to existing tests MUST be justified by approved
requirement changes or verified test defects.

Lightweight execution evidence MUST demonstrate that relevant behavioral tests failed
before implementation and passed afterward. TDD execution evidence MUST associate
relevant Red and Green results with identifiable implementation states and their
execution order. Evidence MUST be sufficient to review test-first chronology; test
output alone, without revision or state association, MUST NOT be treated as conclusive
proof of TDD.

Evidence MUST distinguish acceptance-first verification from subsequent inner-layer
TDD activity where inner cycles are performed. Consolidated evidence MAY be used,
provided the relevant behavioral increments and their test-first chronology remain
identifiable. Exhaustive per-behavior execution histories, intermediate source
snapshots, and separate no-refactor artifacts are NOT required. Evidence storage,
retention, and revision-association mechanisms MUST be established in shared
project-level decisions.

Final acceptance tests, regression tests, coverage requirements, architecture fitness
tests, static analysis, and contract verification remain mandatory. Passing tests and
coverage alone MUST NOT be presented as proof that TDD was followed.

### IV. Automated Architecture and Coverage Verification

Automated architecture fitness tests MUST enforce dependency direction, Core
independence from concrete Infrastructure and Transport Adapters, Domain isolation
from external frameworks and Adapters, and boundary contract and type isolation.
Architecture fitness verification MUST distinguish properties enforced by automated
structural checks from those requiring behavioral contract tests or explicit review.
Passing dependency checks alone MUST NOT be represented as verification of semantic
boundary isolation.
These checks MUST preserve the Application framework permission in Principle I.
Violations MUST fail the relevant checks. Automated behavioral tests MUST verify
Domain invariants during construction, reconstitution, and state transitions where
applicable. Construction tests MUST verify supported APIs enforce applicable
invariants, including entity-level cross-field constraints, and return explicit
outcomes for expected creation failures, including Value Object validation failures.
Construction checks MUST verify that every Value Object and Entity exposes the
normal-creation factory API and that callers outside Domain construction internals
use supported factories or reconstitution APIs rather than internal constructors.
These checks MUST enforce supported API use
without requiring language-level absolute constructor privacy. Reconstitution tests
MUST verify persisted-state invariants and, where creation-only eligibility rules
exist, verify that restoring otherwise valid state does not reapply those rules.
Architecture checks MUST allow Persistence Adapters to invoke controlled Domain
reconstitution directly when implementing Core-owned Ports.

Every new or modified business-logic function or method MUST achieve 100% branch
coverage, measured by automated tooling. The minimum coverage measurement unit MUST
be the entire affected function or method, including its unchanged measurable
branches, rather than only newly introduced or modified branches. Applicable Domain
and Application business logic MUST be included.

Functions or methods with no measurable branches MUST still satisfy applicable
behavioral testing requirements. Branch coverage alone MUST NOT be treated as
sufficient verification or as proof of behavioral correctness or complete business
scenario coverage.

Feature Plans MUST apply project-wide coverage tooling and exclusion policy and
identify the applicable coverage scope and justified exclusions, but MUST NOT weaken
the constitutional minimum. Coverage exclusions MUST be explicitly justified and
MUST NOT conceal untested business behavior.

### V. Evidence-Based Completion

Before declaring a feature complete, all applicable mandatory checks MUST run
against the final implementation state, pass, and have their required evidence
available. Failed, skipped, blocked, or unexecuted mandatory checks MUST be reported.
Agents MUST NOT claim completion from self-assessment, incomplete verification,
or results that do not match the final implementation state.

The project MUST define and enforce automated static quality checks through shared
project-wide tools, rules, and configurations. Feature Plans MUST apply these policies.

## Architecture Decisions and Open Questions

Architectural decisions that affect multiple features MUST be established and
maintained as shared project-level decisions for common implementation conventions
and tooling; this constitution defines mandatory project-wide principles. Feature Plans
MUST follow these decisions and MUST NOT independently override them. Feature-specific implementation
decisions MAY remain in Feature Plans. Changes to established project-wide decisions
MUST be explicitly reviewed and recorded; constitutional changes MUST also follow
the amendment procedure.

Unresolved shared decisions, including Port ownership, Application framework
dependencies, architecture fitness tooling, and construction API conventions, MUST
be resolved at project level before implementation depends on them. Unrelated work
MAY proceed while those decisions remain open.

The following project-wide decisions remain unresolved in this constitution. Existing
repository policies and tooling MUST be assessed before treating a decision as absent;
any established decision MUST be referenced rather than independently replaced.

- TODO(PORT_OWNERSHIP): Establish consistent criteria for Domain versus Application
  Port ownership and stable cross-context communication and transaction-boundary rules.
- TODO(APPLICATION_FRAMEWORKS): Establish the allowed Application framework dependency
  policy, including permitted framework-owned types in public contracts.
- TODO(CONSTRUCTION_CONTRACTS): Establish common factory and reconstitution naming,
  signatures, and outcome conventions for Value Objects and Entities, including
  representation and propagation of persisted-state data-integrity failures.
- TODO(QUALITY_TOOLING): Confirm and document shared architecture-fitness, static
  analysis, and coverage tooling and configurations; stable module boundaries;
  and which architectural rules require behavioral verification or review.
- TODO(TDD_SCOPE): Define the project-wide treatment of behavior-preserving refactors,
  generated code, configuration, and exploratory work.
- TODO(APPROVAL_AUTHORITIES): Identify specification approval and coverage-exclusion
  approval authorities and the shared criteria for permissible exclusions.
- TODO(TDD_EVIDENCE): Establish shared evidence location, retention, revision
  association, invalidation, and review policies.

## Development Workflow and Quality Gates

1. Specifications MUST state the business behavior used to derive acceptance tests.
2. Plans MUST reference applicable project-wide decisions, identify responsibilities
   across Domain, Application, Ports, and Adapters, and report unresolved shared
   decisions that block dependent implementation. Plans MUST NOT redefine shared policy.
3. Plans MUST specify feature-level transaction coordination, concrete boundary
   contracts and conversions, acceptance-test boundaries and environments, and
   applicable coverage scope and checks under shared policy. For affected Domain
   types, plans MUST identify factory and reconstitution APIs, accepted Domain Types,
   type-level and entity-level invariants, creation-only eligibility, and invalid
   persisted-state outcomes. Language-specific implementation mechanisms MAY vary.
4. Tasks and implementation MUST preserve test-first ordering and record execution
   evidence as defined in Principle III, which MAY be consolidated across cohesive
   increments.
5. Completion review MUST inspect architecture checks, invariant and acceptance tests,
   regression tests, coverage, static checks, contract verification, and TDD evidence
   against the final implementation state.
   Any missing or failing mandatory check prevents a successful completion claim.

## Governance

Ratified constitutional requirements govern feature specifications, plans, tasks, and
implementation. Those artifacts MUST comply with the effective ratified version.
Proposed amendments MUST be identified as proposed and MUST NOT be represented as
effective policy. Until a proposal is ratified, the last ratified version remains
effective. Unresolved questions above MUST NOT be treated as settled policy.

The Project Owner is the constitutional approval authority. Amendments MUST document
the proposed text, rationale, compatibility impact, and migration requirements.
Before marking an amendment as ratified, its permanent amendment-log entry MUST
record explicit Project Owner approval, the actual approval date, and a durable
reference to the approval statement. Inferred intentions, typos, revision instructions,
automated checks, and commits MUST NOT be treated as explicit ratification approval.
Once explicit approval is given, the version status and permanent Amendment Log in
`amendments.md` MUST be updated together to record ratification consistently.

Versions MUST use semantic versioning: MAJOR for incompatible principle removals or
redefinitions; MINOR for new principles or materially expanded guidance; PATCH for
non-semantic clarifications and corrections. A MAJOR classification MUST identify
the specific incompatibility with an existing principle; implementation migration
alone MUST NOT automatically imply a MAJOR change. Each new amendment MUST receive
a version under this policy and an amendment date. Revisions to the same unratified
proposal MAY retain its proposed version and MUST update its amendment date and log.

Specifications, plans, and completion reviews MUST assess compliance and explicitly
report deviations; a plan alone MUST NOT waive a mandatory constitutional rule.

Permanent amendment history and approval evidence MUST be maintained in
[amendments.md](amendments.md), including version, amendment date, summary and rationale,
compatibility impact, migration requirements, and approval status. Actual approval dates
and durable evidence references MUST be recorded when available; missing historical
records MUST NOT be invented. Amendment review and ratification MUST consult this log.
Ordinary feature development MUST NOT require loading amendment history.

**Version**: 2.1.0 | **Ratified (original adoption)**: 2026-10-21 | **Last Amended**: 2026-10-22

**Status**: Proposed — awaiting Project Owner approval; not effective policy.

**Last Historically Recorded Ratified Version**: 2.0.0 (`2b51fcd`).
