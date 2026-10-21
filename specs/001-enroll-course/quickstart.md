# Quickstart Validation Guide: Python 3.12 / GraphQL

Run these validation commands from the repository root. Python packaging uses the Hatchling PEP 517 backend, with both schemas included in the wheel. See [README](../../README.md) for host identity integration and explicit schema initialization. SQLite must reside on a local filesystem with reliable locking.

## Prerequisites and setup

Use Python 3.12, uv, a writable local temporary directory and dependency-download access for the initial sync. Commit uv.lock and use it for repeatable runs. No Java, external database, container or real identity provider is needed for tests. Production requires a host-supplied identity verifier and fails closed if none is configured; deterministic test credentials never activate production authentication.

```bash
uv sync --frozen --dev --python 3.12
uv run python --version
uv run pytest tests/acceptance -q
```

Expected: Python 3.12 and all fifteen specification scenarios exercised through HTTP POST `/graphql`, using pytest, Flask app.test_client(), real graphql-core schema execution, credential headers, a deterministic verifier double and file-backed SQLite. Fixtures create existing records directly; no production record-management API is added. Fresh connections verify durable state. See [contract](contracts/enrollment-api.md), [SDL](contracts/schema.graphqls) and [data model](data-model.md).

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

For each independently testable behavior select its acceptance example, execute the expected behavioral Red before production edits, then follow that failure into inner Red/Green/Refactor cycles as needed. Import/configuration failures do not count as Red. Preserve raw output, exit codes, execution order and source associations. When no refactor is needed record the rationale and rerun relevant tests. Focused passes cannot substitute for final checks.

## Acceptance expectations

| Spec scenarios | Expected result |
|---|---|
| 1–2 | Eligible/shared course -> EnrollCourseSuccess; exactly one pair persists after close/reopen |
| 3 | Pause before transaction acquisition, commit membership/offering change on another connection, resume -> COURSE_NOT_OFFERED. Complement: change attempted after BEGIN IMMEDIATE waits until enrollment commits, and does not retroactively invalidate it |
| 4–6 | Application handles Student/Programme/Course repository misses -> corresponding Core-defined rejection; no dependent lookup or trivial Domain existence guard |
| 7 | Domain offering policy rejects an existing course not offered by the existing programme -> COURSE_NOT_OFFERED |
| 8–9 | Existing pair or lost response after confirmed commit -> ALREADY_ENROLLED unless a higher-priority reason applies; saved pair unchanged |
| 10 | Two overlapping HTTP requests, separate connections -> one success, one ALREADY_ENROLLED, one pair |
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

Review Core signatures to keep Application missing-record types/result union out of Domain and preserve explicit adapter conversions. Measure whole Application orchestration functions, including verification success/failure and every existence/short-circuit branch, plus whole Domain policy methods under the unchanged 100% statement-and-branch gate. Keep executed Outside-In Red/Green/Refactor evidence for both responsibilities.

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

Keep per-increment evidence under `specs/001-enroll-course/evidence/<increment>/`, including commands, output/exit codes, execution order, test identity, source revision and working-tree diff digest. Final manifest binds complete results to a source/config/test digest excluding evidence/build output. Later edits invalidate affected results and require final reruns. Reviewer inspects actual transcripts. Failed, skipped, blocked or missing mandatory checks prevent a feature-completion claim.
