# Constitution Amendment History

This permanent record is separate from the current constitution. Amendment review and
ratification must consult it; ordinary feature development does not require it.
Missing approval records and dates are not inferred from version labels or commits.

## 2.0.0 — Historically recorded ratified baseline

- Amendment date: 2026-10-21, as recorded in `2b51fcd`.
- Summary and rationale: cohesive TDD increments and consolidated evidence reduce
  unnecessary recording while retaining final quality gates.
- Compatibility impact: replaced 1.4.0's per-behavior granularity; its historical MAJOR
  classification is retained without retrospective reclassification.
- Migration requirements: align task sequencing and evidence with cohesive increments.
- Approval status: historically recorded as ratified; explicit approval evidence was
  not recovered. TODO(HISTORICAL_APPROVAL): recover the original approval record.
- Approval date and evidence: explicit approval date unknown. Commit `2b51fcd` records
  the historical version and amendment date, not proof of Project Owner approval.
- Original ratification date (historical): 2026-10-21, preserved from the constitution.

## 2.1.0 — Proposed amendment

- Amendment date: 2026-10-22.
- Summary and rationale: consistent construction contracts, separate reconstitution,
  clear validation ownership, shared decisions, and durable amendment governance.
  This review separates history from recurring constitutional context and classifies
  invalid persisted state as a data-integrity failure.
- Compatibility impact: proposed MINOR classification assessed against 2.0.0's
  existing definitions: MAJOR for incompatible principle removals or redefinitions;
  MINOR for new principles or materially expanded guidance; PATCH for non-semantic
  clarifications and corrections. This proposal expands API and governance guidance
  without removing or redefining the prior inward-dependency, invariant-ownership,
  explicit-failure, TDD, coverage, or completion principles. Restricting supported
  normal creation to factories entails API migration; that alone does not establish
  an incompatible principle redefinition. No concrete contradiction requiring a new
  version number was identified. This assessment does not rely on the proposal's
  added migration/versioning explanation.
- Migration requirements: route normal creation for Value Objects and Entities through
  factories; retain controlled Adapter-callable reconstitution; verify explicit
  expected-failure outcomes and supported API use without absolute constructor privacy;
  classify invalid persisted state under a shared data-integrity error contract;
  consolidate shared decisions and approval records. Application migration has not
  been performed by this documentation revision.
- Approval status: **Proposed — awaiting Project Owner approval**. Not effective policy;
  2.0.0 remains the last historically recorded ratified version.
- Approval date and durable evidence reference: unavailable; explicit approval has
  not been verified. Actual approval statement, date, and durable reference must be
  recorded before ratification, with constitution metadata updated consistently.

### Correction of the prior ratification claim — 2026-10-22

The prior amendment log claimed “Ratified — approved by the Project Owner on
2026-10-22” based on the message “gratify the constitution” in this conversation.
The assistant interpreted that wording as an instruction to ratify. This was an
inference from a typo, not verified explicit approval. The claimed approval date is
preserved here as a superseded claim, not an actual approval date. No durable explicit
approval reference is available. The present review restores Proposed status as
requested, without inventing retrospective approval or erasing the earlier claim.

### Scope retained from the removed temporary Sync Impact Report

The following report is archived verbatim. Its ratification claims are superseded
by the correction above; it is not approval evidence or effective policy.

```text
Sync Impact Report (temporary review material; remove before committing)
Version change: 2.0.0 → ratified 2.1.0 (MINOR: expanded construction, boundary,
  and governance guidance; no incompatible principle removal or redefinition identified).
Current revision: proposed 2.1.0 → ratified 2.1.0 (version retained as requested).
Approval status: ratified by Project Owner instruction in this conversation on 2026-10-22.
Modified principles:
- I. Hexagonal Architecture and Inward Dependencies: clarify direct Adapter
  adaptation through supported Domain creation and reconstitution APIs.
- II. Domain Ownership, Integrity, and Boundary Contracts: require factories for
  normal Value Object and Entity creation; separate controlled reconstitution;
  clarify validation and authorization coordination.
- III. Outside-In Test-Driven Development: apply shared policies in feature planning.
- IV. Automated Architecture and Coverage Verification: verify supported API use
  without absolute constructor privacy; apply project-wide coverage policy.
- V. Evidence-Based Completion: establish static quality tooling at project level.
Added sections: Domain Construction Contracts and Reconstitution within Principle II;
  project-wide decision rules; permanent amendment log within Governance.
Removed sections: redundant open-question restatements; feature-specific planning
  details moved to Development Workflow and Quality Gates.
Compatibility/migration: replace normal-creation constructor calls with factories
  for Value Objects and Entities; preserve separate Adapter-callable reconstitution;
  verify explicit expected-failure outcomes; consolidate shared policies and approval
  records. Implementation migration alone does not imply a MAJOR version change.
Follow-up TODOs: PORT_OWNERSHIP, APPLICATION_FRAMEWORKS, CONSTRUCTION_CONTRACTS,
  QUALITY_TOOLING, TDD_SCOPE, APPROVAL_AUTHORITIES, TDD_EVIDENCE,
  HISTORICAL_APPROVAL. Only the constitution was modified.
Permanent amendment records below MUST remain when this temporary report is removed.
```
