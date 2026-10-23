# ADR-0001: Repository-confirmed Entity identities and conditional Student replacement

**Date**: 2026-10-22
**Status**: Feature design decision; implementation pending
**Authority**: [Constitution v3.0.0](../../../.specify/memory/constitution.md), [specification](../spec.md) FR-015–FR-018, and the user's revision instructions. This ADR records implementation decisions within those constraints; it does not amend them.

## Context

Current Application operations construct complete Student/Enrollment Entities before persistence confirms their identities. Student replacement is unconditional and carries no saved version. Constitution v3.0.0 requires Repository-controlled construction with persistence-confirmed identities; FR-018 requires explicit rejection of stale replacements.

The preceding design added an identity reservation table and active/committed/revoked Entity lifetime handles. SQLite's existing key constraints and transactions can confirm identities and keep creation atomic. Keeping new Entities within the creation operation until the transaction outcome is known avoids adding transaction state to Domain.

## Decision

### 1. Keep Repository-controlled construction and existing identities

Repository remains the production entry point for creating and restoring complete Entities through Core-owned Ports. Keep externally supplied StudentId, ProgrammeId and CourseId, and the existing programme-course and student-course composite identities. Application validates supplied representations through Value Object factories; it does not generate identities or construct complete Entities.

Domain owns `Entity.create()` and its creation-specific rules. `Entity.reconstitute()` enforces persisted-state validity without replaying creation-only eligibility. Repository coordinates persistence and these Domain operations. Domain has no dependency on SQLite, Repository implementations, sessions or transaction status.

### 2. Confirm identity by INSERT within the enclosing transaction

1. Application validates input, sequences the required Domain policies and invokes Repository.
2. The Repository participates in the transaction managed by the Unit of Work. The Unit of Work controls transaction initiation, commit, and rollback. The SQLite adapter uses `BEGIN IMMEDIATE` before use-case reads.
3. Repository inserts the supplied state into the business table. Successful INSERT acknowledges the identity/state association under existing primary-key/unique constraints. Obtain the confirmed natural/composite identity from that inserted state; validating or generating an ID alone is insufficient.A successful INSERT confirms the identity within the active transaction, but the Entity is not considered successfully created or persisted until the enclosing transaction commits.
4. Repository invokes `Entity.create()` with the confirmed identity and validated Domain values. The uncommitted row is intermediate persistence state until Domain accepts it; INSERT success does not replace Domain creation rules.
5. Any explicit Domain rejection, unexpected exception or persistence failure causes the enclosing transaction's uncommitted changes to roll back. Do not commit an earlier part of a failed creation operation.
6. Application reports success and returns the Entity only after the enclosing transaction commits successfully. Repository MUST NOT independently commit.

Remove the dedicated identity reservation table and all associated allocation, cleanup, finalization and recovery mechanisms. Do not introduce `CreationData`, ID generator Ports, surrogate identities or replacement reservation mechanisms. Ordinary INSERT must reject duplicates; do not use INSERT OR REPLACE or ignore a failed insertion.

### 3. Keep transaction outcome outside Entities

Remove Entity lifetime handles and Entity-level transaction lifecycle tracking. Newly constructed Entities remain local to the creation operation until commit is confirmed. They must not be published, cached, retained for later business use, or used to trigger externally visible effects before that point. On failure, discard the operation's pending Entity/result references and do not make canceled Entities available for further business use. This is an orchestration boundary, not an Entity revocation API.

A failed or uncertain transaction never returns a successful creation result. If commit is uncertain, return a technical completion failure requiring reconciliation through a later independent read/operational check. Do not assume that rollback or deletion is safe, delete/revert potentially committed complete records, or automatically repeat the write. Rollback is appropriate only for a transaction known to remain active and uncommitted. A confirmed commit survives response loss or subsequent cleanup errors.

Cleanup faults remain technical failures: preserve an already-propagating unexpected exception and retain secondary diagnostics; if cleanup fails while an ordinary outcome is pending, return the existing technical failure rather than claim verified transaction termination. These responsibilities belong to Application/UoW and persistence resource handling, not Domain Entities.

### 4. Preserve conditional Student replacement

Keep Domain `SavedVersion` as a strict positive signed-64 integer and the trusted host's `StudentSnapshot(student, SavedVersion)`. It carries concurrency metadata from one saved state; StudentId still defines Entity equality/hash.

New Student rows start at version 1. Every committed full replacement advances the version by exactly one, including unchanged-detail replacement. Repository invokes the controlled Domain detail transition and performs one guarded update matching StudentId and the required expected version, advancing the version atomically. A stale version returns an explicit outdated-version conflict. No automatic retry, silent refresh, merge or unconditional replacement is allowed; callers reload before resubmitting. Rejection or confirmed rollback preserves committed details and version. Version exhaustion is a technical failure without wraparound.

Preserve validation/rejection order: StudentId → ProgrammeId → name → email → mode → required replacement-version validity → target existence → outdated-version policy → email-availability policy. Preserve enrollment FR-009/FR-014 ordering and its existing bounded pair-conflict replay; it does not authorize retrying stale Student replacement.

### 5. Retain version compatibility requirements

Fresh schema retains the five business tables and adds Student version constraints and the version-advancement guard. There is no reservation schema. Inspect existing schema compatibility before writes and refuse incompatible schemas unchanged; automatic migration/backfill remains outside scope. Hosts must adopt snapshot retrieval and expected-version replacement. The guard prevents accepted updates from leaving versions unchanged; raw SQL privileges are not an authorization boundary or proof of caller intent.

## Alternatives considered

| Alternative | Reason not selected |
|---|---|
| Application constructs Entities or generates IDs before persistence | Does not establish persistence-confirmed identity or the required Repository entry point. |
| Dedicated identity reservation table | Existing business-table keys and an uncommitted INSERT provide confirmation without a second allocation/finalization protocol. |
| Active/committed/revoked Entity handles | Adds persistence lifecycle state to Domain; operation confinement and the commit boundary provide the required exposure behavior. |
| Repository commits each creation independently | Splits the enclosing use case and violates transaction ownership. |
| Storage constraints replace Entity.create | Omits Domain-owned creation decisions; an accepted INSERT remains rollback-capable until those rules pass. |
| Timestamp/hash versions or last-write-wins replacement | Can reuse tokens or overwrite newer details, contrary to FR-018. |
| Reload and automatically retry a stale Student replacement | Reapplies old intent to newer details without caller review. |
| Automatic legacy database migration | Outside the approved feature scope. |

## Consequences

Complete Entity construction remains intentionally coupled to persistence through Repository. This accepted constitutional trade-off guarantees confirmed identity while Domain retains creation rules and remains independent of persistence technology. INSERT precedes Domain construction, so Domain rejection must roll back real writes; constraints provide storage protection without replacing Domain admission.

The design removes a table and Entity lifecycle machinery. Application/UoW must keep pending results local and enforce the commit boundary. Entities do not detect transaction cancellation themselves. Snapshot metadata and mandatory expected versions require trusted host updates; GraphQL is unchanged.

## Validation

Real SQLite contracts and acceptance tests must verify observable behavior:

- INSERT confirms the actual natural/composite identity before factory invocation, and Domain creation rules execute before successful commit.
- Explicit Domain rejection or exception after INSERT leaves no committed Entity; insertion/commit failures return no successful creation result.
- Duplicate identities are rejected by existing database constraints, with precise conflict translation and no overwrite.
- Repository does not independently commit preceding or following writes in the enclosing use case.
- Pending Entities/results stay inside the operation; failed or uncertain transactions expose no successful or reusable canceled creation result.
- Uncertain commit returns technical failure requiring reconciliation, with no destructive compensation or automatic write retry.
- Restoration produces valid Entities from saved identities without replaying creation-only rules; corrupt saved state remains a technical integrity failure.
- Conditional replacement prevents stale overwrites; creation version 1, replacement advancement, rejection precedence and rollback/version preservation remain correct.

Use controlled factory rejection where valid typed inputs currently have no additional rejecting business case; do not invent a Domain rule. Remove reservation/finalization/recovery and Entity-handle state/revocation tests. See [plan](../plan.md), [research](../research.md) and [Repository contract](../contracts/repository-lifecycle.md).

## Sources

SQLite documents [primary-key/unique constraints](https://www.sqlite.org/lang_createtable.html#constraints) and [transactions](https://www.sqlite.org/lang_transaction.html). Python 3.12 documents [sqlite3 transaction control](https://docs.python.org/3.12/library/sqlite3.html#transaction-control-via-the-autocommit-attribute). With this adapter's `autocommit=True`, explicit SQL controls the enclosing transaction. INSERT-before-factory ordering and operation confinement are project design choices under the constitution/specification.
