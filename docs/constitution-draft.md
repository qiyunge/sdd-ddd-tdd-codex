# Project Constitution

**Version:** 1.0.0  
**Status:** Final Draft

---

## I. Architecture Governance

### 1. Core Architecture and Dependency Direction

1. The system MUST follow Hexagonal Architecture, with its Core internally organized according to Clean Architecture dependency principles.

2. The Hexagonal Core MUST consist of:
   - **Application (Outer Core):** Responsible for use-case orchestration and coordination.
   - **Domain (Inner Core):** Responsible for domain models, business decisions, state transitions, and invariants.

3. Dependencies MUST point inward:
   - Application MAY depend on Domain.
   - Infrastructure and Transport Adapters MAY depend directly on Application and/or Domain.
   - Domain MUST NOT depend on Application, Infrastructure, or Transport.
   - Application MUST NOT depend on concrete Infrastructure or Transport Adapters.

4. Application MUST NOT be treated as a mandatory gateway to Domain. External Adapters MAY directly use public Domain types and construction mechanisms.

5. Core operations requiring external capabilities MUST access them through Core-owned Ports rather than concrete Adapter implementations.

### 2. Framework Independence and Application Flexibility

1. Domain MUST remain independent of application frameworks, persistence frameworks, transport technologies, and external service SDKs.

2. Application MAY use external libraries and frameworks for orchestration, coordination, validation, and other application-level responsibilities.

3. Framework usage MUST NOT reverse architectural dependencies or relocate domain business decisions outside Domain.

### 3. Domain-Driven Design Responsibilities

1. Domain business decisions, state transitions, and invariants MUST reside in Domain.

2. Application MUST orchestrate use cases without duplicating or overriding domain business decisions.

3. Adapters MUST NOT independently implement domain business decisions belonging to Domain.

4. Domain modeling decisions MUST be driven by business requirements rather than Infrastructure or Transport representations.

### 4. Domain Integrity and Application State

1. Domain entities and value objects MUST preserve their invariants throughout construction, reconstitution, and state transitions, regardless of the caller.

2. Application MAY hold unvalidated, incomplete, or invalid input and intermediate states during orchestration, validation, and error handling. Such states MUST NOT be represented as valid Domain objects.

3. Domain MUST NOT rely on Application, Adapters, or external validation to enforce its invariants.

### 5. Full Bridge Boundary Isolation

1. Architectural boundaries MUST use explicit contracts and conversions where representations differ, preventing unintended coupling.

2. Infrastructure and Transport representations MUST NOT leak into the Core.

3. External Adapters MAY directly use public Domain types, provided Domain invariants and dependency rules are respected.

4. Conversion from external representations into Domain types MUST preserve Domain invariants.

5. Application MAY use Domain types internally. Redundant mappings and wrapper types MUST NOT be required solely to satisfy architectural layering.

### 6. Architecture Verification

1. Architectural dependency and boundary constraints MUST be enforced through automated architecture fitness tests.

2. Architecture fitness tests MUST verify:
   - Core independence and dependency direction.
   - Domain isolation from external frameworks and Adapters.
   - Boundary contract and type isolation.

3. Domain invariant preservation MUST be verified through automated behavioral tests, including construction, reconstitution, and state transitions where applicable.

4. Architecture violations MUST cause the relevant verification checks to fail.

---

## II. Test-Driven Development Governance

### 1. Mandatory Outside-In TDD

1. All new or modified business behavior MUST be developed using Outside-In Test-Driven Development.

2. Feature development MUST begin with executable acceptance tests derived from the approved specification.

### 2. Layer-Specific Test-First Development

1. Each affected architectural layer, including Application, Domain, and Adapters, MUST have its responsibilities verified by appropriate automated tests.

2. Production behavior in each affected layer MUST be driven by failing tests.

3. Test scope and granularity MUST reflect the responsibilities and risks of the affected layer.

4. Tests MUST verify observable behavior and architectural responsibilities rather than implementation details.

5. Separate test files or test classes MUST NOT be required solely to mirror production code structure.

### 3. Red–Green–Refactor Discipline

Each independently testable behavior increment MUST follow Red → Green → Refactor:

- **Red:** Write and execute a test that fails for the expected behavioral reason before implementing the corresponding production behavior.
- **Green:** Implement the minimum production code necessary to make the test pass.
- **Refactor:** Improve the design where appropriate while preserving behavior, then rerun relevant tests.

A failure caused solely by test infrastructure, configuration, or unrelated defects MUST NOT count as a valid Red phase.

### 4. Test Integrity

1. Tests MUST NOT be weakened, deleted, skipped, or modified solely to make an implementation pass.

2. Changes to existing tests MUST be justified by approved requirement changes or verified test defects.

### 5. TDD Process Verification

1. TDD compliance MUST be supported by recorded test execution evidence documenting the Red → Green → Refactor sequence.

2. Evidence MUST include executed commands, observed results, execution order, and relevant failure information.

3. Agent-generated summaries without corresponding execution evidence MUST NOT satisfy process verification.

---

## III. Test Coverage Governance

### 1. Branch Coverage Requirement

New or modified business logic MUST achieve 100% branch coverage.

### 2. Coverage Measurement

1. Branch coverage MUST be measured using automated tooling.

2. Coverage measurement MUST include all applicable new or modified business logic.

3. The scope of business logic subject to coverage requirements, including applicable Application and Domain code, MUST be explicitly defined during planning.

### 3. Coverage Integrity

1. Coverage exclusions MUST be explicitly justified and MUST NOT be used to conceal untested business logic.

2. Coverage metrics MUST NOT be treated as proof of behavioral correctness or complete business scenario coverage.

---

## IV. Verification and Completion Governance

### 1. Final Verification

Before declaring a feature complete, all applicable mandatory verification checks MUST be executed against the final implementation state.

### 2. Completion Criteria

A feature MUST NOT be declared complete unless all applicable mandatory verification checks pass and their required evidence is available.

### 3. Verification Integrity

1. Failed, skipped, blocked, or unexecuted mandatory checks MUST be explicitly reported.

2. An Agent MUST NOT claim successful feature completion based on self-assessment, incomplete verification, or results that do not correspond to the final implementation state.

### 4. Static Quality Verification

1. The project MUST define and enforce applicable automated static code quality checks.

2. The specific tools, rules, and configurations MUST be established during planning.

---

## Governance

This Constitution establishes mandatory architectural, development-process, test-coverage, and verification constraints.

Amendments, versioning, and compliance procedures MUST follow the project's Spec-Kit Constitution governance process.

All feature specifications, implementation plans, tasks, and implementation activities MUST comply with the currently effective Constitution.

**Version:** 1.0.0