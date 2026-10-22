# Quickstart Validation Guide: Python 3.12 / GraphQL

Run these validation commands from the repository root. Python packaging uses the Hatchling PEP 517 backend, with both schemas included in the wheel. See [README](../../README.md) for host identity integration and explicit schema initialization. SQLite must reside on a local filesystem with reliable locking.

## Prerequisites and setup

Use Python 3.12, uv, a writable local temporary directory and dependency-download access for the initial sync. Commit uv.lock and use it for repeatable runs. No Java, external database, container or real identity provider is needed for tests. Production requires a host-supplied identity verifier and fails closed if none is configured; deterministic test credentials never activate production authentication.

```bash
uv sync --frozen --dev --python 3.12
uv run python --version
uv run pytest tests/acceptance -q
```

Expected after implementing the extension: Python 3.12 and all fifteen enrollment specification scenarios exercised through HTTP POST `/graphql`, using pytest, Flask app.test_client(), real graphql-core schema execution, credential headers, a deterministic verifier double and file-backed SQLite. Fixtures create existing records directly; no production record-management API is added. Fresh connections verify durable state. See [contract](contracts/enrollment-api.md), [SDL](contracts/schema.graphqls) and [data model](data-model.md).

An app-factory fixture creates an isolated Flask app with injected dependencies and a client. Use client.post with JSON and credential headers; a bare request_context does not exercise full dispatch. Each concurrent worker gets its own client/context. A separate fixture starts Waitress on a local ephemeral port for server smoke/concurrency tests and shuts it down afterward. Flask test-client dispatch proves HTTP application behavior but does not by itself prove socket handling or worker scheduling. Pure Core tests do not start a server.

Direct engine tests load the SDL with build_schema, verify schema validity and execute documents with graphql_sync(check_sync=True). These complement HTTP acceptance and never replace credential/header/routing validation. The installed distribution is graphql-core; its import namespace is graphql. Lock the selected 3.3 minor release.

## Focused development feedback

```bash
uv run pytest tests/domain -q
uv run pytest tests/application -q
uv run pytest tests/adapters -q
uv run pytest tests/architecture -q
uv run pytest tests/acceptance -q
```

Choose a cohesive behavioral increment guided by acceptance examples. Execute relevant
behavioral tests and retain their expected failure before implementation; implement
the required behavior and verify relevant tests pass. Consider refactoring and keep
relevant tests passing; no code change or separate no-refactor artifact is needed
when none is warranted. Related behaviors may share one cycle and tests may span
layers through a shared behavioral boundary. Import/configuration failures do not
count as Red. Lightweight commands/results may be consolidated across increments;
passing tests and coverage alone do not prove TDD. Focused passes do not replace
mandatory final checks.

## Acceptance expectations

| Spec scenarios | Expected result |
|---|---|
| 1–2 | Eligible/shared course -> EnrollCourseSuccess; exactly one pair persists after close/reopen |
| 3 | Pause before transaction acquisition, commit membership/offering change on another connection, resume -> COURSE_NOT_OFFERED. Complement: change attempted after BEGIN IMMEDIATE waits until enrollment commits, and does not retroactively invalidate it |
| 4–6 | Application handles Student/Programme/Course repository misses -> corresponding Core-defined rejection; no dependent lookup or trivial Domain existence guard |
| 7 | Domain offering policy rejects an existing course not offered by the existing programme -> COURSE_NOT_OFFERED |
| 8–9 | Existing pair or lost response after confirmed commit -> ALREADY_ENROLLED unless a higher-priority reason applies; saved pair unchanged |
| 10 | Two overlapping HTTP requests, separate connections -> one success, one ALREADY_ENROLLED when the saved pair is visible, one pair. When a conflict is detected and one full re-evaluation still cannot observe that pair, the loser is PERSISTENCE_FAILURE and the saved pair remains |
| 11 | Inject failure during insert/before commit with actual rollback -> PERSISTENCE_FAILURE; no partial row |
| 12 | Existing enrollment and absent offering -> ALREADY_ENROLLED; offering port not invoked |
| 13 | Negative verification -> Application returns Core DENIED; ownership and persistence spies fail on any invocation |
| 14 | Verified actor/target mismatch -> Domain ownership returns identical DENIED; persistence spy fails on any session/lookup access |
| 15 | Invalid attempt overlaps unrelated eligible request -> invalid attempt mutates nothing; valid request persists its own pair |

Also cover combined failures proving full precedence, zero offerings, verified identity without Student, Domain construction/reconstitution/transitions, invalid row conversion, all union mappings, schema errors/nullability/ID coercion, explicit camelCase field and enum mapping, all union type names, operationName/variables forwarding, unexpected awaitable detection, sanitized technical errors, no lazy output reads and unchanged prerequisite records. HTTP 200 alone is never enrollment success. Attribute concurrent mutations to their own operations rather than demanding a globally unchanged database.

Use independent threads/connections and bounded events/barriers, not sleeps. Each worker creates, uses and closes its own connection; never share a connection or disable same-thread checks to evade ownership. Do not require a two-party barrier after a single-writer lock. Test the configured BEGIN IMMEDIATE actually precedes reads; explicitly test SQL COMMIT/ROLLBACK with autocommit=True, connection close, lock timeout and failure classification. Never use response loss as evidence of rollback or compensate/delete a committed pair. Use a controlled legacy fixture or a port test for missing-record-plus-existing-pair cases that restrictive production foreign keys prevent creating; do not weaken production constraints for fixtures.

Flask HTTP adapter tests also cover 404 paths, 405 methods/Allow header, 415 media types, malformed JSON/envelope 400 responses, and safe GraphQL error envelopes. Engine exceptions must not expose SQL, credentials, original resolver errors or tracebacks. Verify schema wiring is reused without sharing per-request identity context. Check POST-only behavior including disabled automatic OPTIONS, no unused static route, JSON error handlers preserving status/Allow headers, and sanitization with production-like exception handling (not only TESTING exception propagation). Core tests must pass with no Flask app/request context; architecture fixtures prove Flask/Werkzeug leakage is rejected.

## Responsibility-specific validation

Application tests drive missing Student, Programme and Course outcomes with repository doubles returning None, and present-record paths with actual validated Domain records. Assert the Core-defined rejection type and no dependent lookup, write or commit on each rejected path. These failures must be driven in Application; do not create trivial Domain None guards or guard-API tests.

Application tests drive failed verification -> DENIED without invoking ownership/persistence, and successful verification -> trusted VerifiedIdentity plus StudentId forwarded to ownership. Domain tests independently drive ownership for matching/mismatched verified identities, duplicate-enrollment rules, course-offering eligibility and Enrollment construction/reconstitution/transitions. Application tests exercise ordered policy delegation and unchanged outcome propagation without duplicating actor equality, duplicate or offering predicates. Branching on a typed policy result to stop is allowed. Existing HTTP acceptance examples retain their exact outcomes and cover combined conditions across both owners. In particular, already-enrolled plus ineligible returns ALREADY_ENROLLED without loading offering data or invoking eligibility.

Review Core signatures to keep Application missing-record types/result union out of Domain and preserve explicit adapter conversions. Measure whole Application orchestration functions, including verification success/failure and every existence/short-circuit branch, plus whole Domain policy methods under the unchanged 100% statement-and-branch gate. Verify both responsibilities; shared behavioral tests may cover them within cohesive increments with lightweight execution evidence.

Verify Domain requires no UnverifiedIdentity model and imports no IdentityVerifier/Application port. Negative verification must not construct a fake Domain identity or target StudentId; validate the target only after verification succeeds, then call ownership. Keep provider-unavailability technical handling separate from an ordinary negative verification result, with zero ownership/persistence calls for both.

## Mandatory final checks

```bash
bash scripts/check-quality.sh
.venv/bin/python -m scripts.assemble_evidence
.venv/bin/python -m scripts.check_evidence
```

First, the quality script executes all tests (including isolated installed-wheel resource and real Waitress socket tests), architecture checks, Import Linter, strict mypy, Ruff lint/format and complete Core coverage. It records raw commands, stdout/stderr, exit codes and digests in `evidence/final/checks/`. It neither reads nor requires a final manifest. Next, assembly writes `evidence/final/manifest.json` with check references, artifact hashes and increment evidence. Finally, validation checks completeness, consistency, scenario counts, Core scope and digest freshness and writes `evidence/final/validation.json`. A quality pass or manifest alone is insufficient. Run all three stages after any source/config/test change. Historical failed raw results are archived rather than discarded.

Configure Python 3.12/static rules, coverage branch=True/fail_under=100 and Import Linter contracts in pyproject.toml. Source directories must include unimported files. Include business behavior outside Core if any is introduced. No business omissions, no cover/no branch suppressions, default exclusions concealing logic or changed-lines gates. Full-scope 100% statement-and-branch coverage meets the entire-function branch minimum; it does not prove complete behavior. Branchless functions still require behavioral tests.

The quality script executes and captures checks tied to the same source/config/test digest. The later evidence validator rejects missing/stale coverage data, empty source/test discovery, skipped mandatory scenarios, unjustified exclusions and missing evidence. Negative fixtures prove detection of a missed business branch, forbidden import/external public type, schema mismatch and skipped required scenario. Server threads remain in the instrumented test process; any future subprocess execution needs explicit coverage collection/combination.

Retain lightweight commands/results and enough test/ordering context to demonstrate
relevant failure before implementation and success afterward. Consolidation across
cohesive increments is permitted. Exhaustive per-behavior histories, intermediate
source snapshots and separate no-refactor artifacts are not required. Final results
must still match the final source/config/test state; changes require final reruns.
Failed, skipped, blocked or missing mandatory checks prevent completion claims.


## Student details extension validation

This section validates the Student-detail operation and tests. Historical enrollment evidence alone does not establish the extension; use current results and the separate current review. Use the pinned environment above; no dependency upgrade is planned. The host must provision valid required details in the new schema before serving. See [student integration contract](contracts/student-details.md) for command/result semantics and [data model](data-model.md) for stored constraints. No new web endpoint is used.

Run the implemented host-integration tests:

```bash
uv run pytest tests/acceptance/test_student_details.py -q
uv run pytest tests/domain tests/application tests/adapters -q
uv run pytest tests/acceptance -q
uv run pytest tests/architecture -q
```

| User Story 2 | Observable result |
|---|---|
| 1 | Valid nonblank name/email accepted and retained exactly after reopen |
| 2 | Invalid normal creation/replacement returns input rejection; corrupt saved details fail reconstitution as data-integrity faults; no invalid Domain object or persisted change |
| 3 | Identical and local/domain/mixed-case variants rejected for another student, including another programme |
| 4 | Whole addresses differing beyond case remain distinct, including plus tags and different domains |
| 5 | Same student's unchanged/case-only email accepted; original submitted case retained |
| 6 | Two workers claim one unused caseless address: one committed success, one typed EmailConflict, no duplicate |
| 7 | Valid replacement succeeds; conflicting replacement preserves every old field |
| 8 | Create for an existing student identity returns the existing-student result, leaves the record unchanged, and is not an email conflict (`student-details-8`) |
| 9 | Replace for a missing student identity returns the missing-student result, creates nothing, and is not an email conflict (`student-details-9`) |
| 10 | A command with more than one defect returns only the first, in the order student identity, programme identity, name, then email (`student-details-10`) |

Add cases for Unicode whitespace such as NBSP and casefold expansion (`Straße@example.com` versus `STRASSE@EXAMPLE.COM`), repeated names, retained surrounding whitespace, invalid ID/detail result distinctions, missing replacement target and duplicate-create ID. No syntax-validation assumptions belong in these tests. Use bounded events and worker-owned connections, with no two-party barrier after the exclusive writer acquisition. Verify unrelated enrollment rows remain unchanged by provisioning.

Exercise SQL constraints on the production schema using configured connections: nonblank fields, duplicate casefold keys on insert/update and registration on every write path. A connection lacking required functions fails closed; no ASCII fallback or forged key is accepted. Verify restoring malformed/corrupt rows produces DataIntegrityFailure(StorageFailure)/PERSISTENCE_FAILURE, while incompatible schemas retain documented technical storage handling without leaking diagnostics. Initialization must refuse a pre-extension schema unchanged, accept a fresh schema and preserve data on compatible repeated initialization; no migration or fabricated defaults.

Before production edits for genuinely missing behavior, capture relevant behavioral
Red with `.venv/bin/python -m scripts.record <increment> red <test-command...>`;
after implementation use the same increment with `green`. Commands run directly,
without shell interpretation. Records retain actual output, exit result and chronology.
See [evidence guide](evidence/README.md). Consider refactoring and rerun relevant tests;
no separate no-refactor artifact or intermediate snapshot is required.

Missing imports, constructor signatures or schema setup alone are not behavioral Red.
Adapt fixtures alongside model/schema changes, preserving approved assertions.

Final manifest assembly/validation requires all 15 enrollment and 7 student-detail scenario identities plus lightweight execution evidence covering changed behavior, consolidated across cohesive increments. Add negative tests showing a missing/skipped new scenario, absent relevant Red/Green evidence, stale final coverage or mismatched final evidence fails validation, plus positive tests accepting consolidated coherent increments without snapshots or no-refactor artifacts. Then execute the three mandatory final commands already listed. Update review notes for this extension; historical manifests and existing green tests alone are insufficient. Complete Core statement/branch coverage, static checks, architecture, installed-package resources and real socket regression tests remain mandatory.

## Failure-contract alignment validation (current feature constraints)

These are required verification scenarios; consult the latest captured results for their actual status.
Use the existing acceptance, focused tests and final evidence commands above after
the revised contracts. Use cohesive Red/Green/Refactor increments covering these behaviors; related items MAY share a cycle:

- Domain Value Object factories return invalid-ID/invalid-text outcomes without raising;
  Entity factories accept validated Domain Types. Ordinary callers use factories and
  separate reconstitution; only explicit internal-misuse tests invoke constructors.
- Application returning INVALID_REQUEST/InvalidStudentDetails via result branches,
  with existing verification/ownership timing and name-before-email ordering.
- Enrollment port PairConflict returned rather than raised; rollback and one complete
  ordered replay; second conflict is technical failure, never guessed duplication.
- Student EmailKeyConflict returned and mapped to EmailConflict; unrelated constraints
  remain technical failures and rejected replacements preserve previous records.
- Provider negative result versus known outage versus injected programming exception:
  respectively DENIED, IDENTITY_UNAVAILABLE, and sanitized internal execution error.
  Neither denial nor provider outage may open persistence.
- Corrupt persisted Domain input becoming PERSISTENCE_FAILURE/StudentStorageFailure, with
  no fake absence, invalid-input or email-conflict result.
- Unexpected programming/contract exceptions propagating through Application to the
  host/transport error boundary, sanitized with diagnostics recorded; cleanup cannot
  overwrite the primary failure or compensate a confirmed commit.

Update port doubles to return conflict outcomes; do not preserve exception-throwing
conflict doubles as the intended contract. Include all changed branches in full Core
coverage and final evidence. Expected GraphQL outcomes still have no GraphQL errors;
unexpected internal execution failures use the sanitized error envelope. Keep the
15 enrollment and 7 Student detail scenario families mandatory.

## StudentEmail equality and identity validation

Use the focused Domain/Application and acceptance commands
above with lightweight Red/Green evidence for cohesive increments covering these behaviors; consider refactoring and keep relevant tests passing:

- Case variants across both address parts compare equal and have equal hashes.
- Unicode expansion pairs (`Straße@example.com`, `STRASSE@EXAMPLE.COM`) compare
  equal and have equal hashes. Verify symmetric equality and consistent inequality.
- A set deduplicates equal StudentEmail values; a dictionary keyed by one can be
  retrieved using an equal variant. Never assert unequal values have unequal hashes.
- Different whole-address keys (including plus tags, domains and significant spaces)
  remain unequal. No trimming or Unicode composition normalization is introduced.
- Comparison with a raw string, StudentName or None does not produce email equality;
  the StudentEmail equality method returns NotImplemented for unrelated types.
- Submitted spelling survives construction, persistence and reconstitution unchanged;
  restored values retain equality/hash behavior.
- Student instances with the same StudentId retain identity/equality after detail or
  programme changes. Different StudentIds remain distinct even with equal email
  values in isolated Domain fixtures; persisted duplicates remain prohibited.
- If Student is hashable, same-ID variants have equal hashes and email replacement
  cannot change its hash. Self-exclusion in uniqueness still compares StudentId.

Consult retained execution records and final results; this guide itself is not execution evidence. Include equality and
hash methods in complete Core coverage and retain the existing acceptance scenario
families and final evidence gates.

## Verification after tooling simplification

Use the acceptance and final-check commands above after implementing the
[evidence capture](plan.md#evidence-capture) and
[architecture fitness](plan.md#architecture-fitness) rules. Positive and
negative cases must establish that consolidated evidence is accepted, genuine
Red/Green remains required, and dependency, isolation and boundary protections remain
effective. Preserve historical execution records unchanged.

Report the [coverage scope](plan.md#coverage-scope)
separately. Retain the configured complete-Core 100% statement-and-branch gate,
source scope and exclusion policy. This guide authorizes no relaxation.

## Constitution v2.3.1 alignment validation

Constitution v2.3.1 is effective. Read [plan.md](plan.md) and the
[construction contract](contracts/domain-construction.md) before migration. No dependency
upgrade, new endpoint, or schema/reason change is planned.

The source-inspected lightweight recorder currently retains output/order but not
implementation-state or acceptance/inner associations. The positional commands above
remain runnable; their current output alone does not satisfy the new chronology contract.
Implement and verify the evidence-capture additions in the plan before using new runs as proof of alignment.
Do not invent new CLI flags, rewrite historical records, or manufacture Red for behavior
that already passes. Historical C1/T050 and Unicode-verification outcomes remain results under their
original baseline. They are not proof of Constitution v2.3.1 compliance.

Validate the migration through the existing focused/acceptance commands and final pipeline:

- Every identifier/text value, VerifiedIdentity and Entity has its supported factory;
  Programme/Course/offering factories remain required even without extra invariants.
  Entity inputs are validated Domain Types; ordinary fixtures/callers avoid constructors.
- Value/record restoration is distinct from normal creation. Invalid persisted state
  yields the internal integrity category and the existing sanitized storage failure,
  never user-input validation, absence or a new business rejection. Restore valid
  enrollment after eligibility changes without replaying creation-only rules.
- Alias-aware allowed/violating construction fixtures establish structural check scope;
  factory/restoration outcomes, converters and ownership are tested behaviorally and
  reviewed semantically. Dependency passes do not establish semantic isolation.
- Positive consolidated/shared-suite evidence has identifiable implementation states,
  actual order, relevant increment/test identities, and acceptance versus inner activity.
  Negative missing associations, unrelated Red/Green, changed-during-run state and stale
  final results fail review/validation. No per-cycle commits, snapshots or refactor
  artifacts become mandatory.

Preserve all 15 enrollment scenarios and the 23 parameterized Student acceptance identities across seven
Student scenario families, including Unicode expansion and composition/non-equivalence.
Also require `student-details-8`, `student-details-9`, and `student-details-10`, plus HTTP
coverage of FR-014 unusable student and course identities as `INVALID_REQUEST`.
Then execute quality capture, current review, manifest assembly and evidence validation
on the final migrated state. Until those pass, report the migration as pending. This
planning guide does not change source, task markers, captured evidence, or completion status.
