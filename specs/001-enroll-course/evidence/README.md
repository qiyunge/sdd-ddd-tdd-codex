# Execution evidence

## Constitution v2.0.0 target policy

Retain lightweight test commands/results demonstrating relevant behavioral failure
before implementation and passing tests afterward. Evidence MAY be consolidated
across cohesive increments, and tests MAY exercise multiple layers through a shared
behavioral boundary. Consider refactoring and verify relevant tests remain passing;
no code changes are required when none are warranted. Exhaustive per-behavior
histories, intermediate source snapshots and separate no-refactor artifacts are not
required. Passing tests and coverage alone do not establish TDD compliance.

## Existing tooling and migration

Current working-tree `record.py` requires `EVIDENCE_REQUEST` JSON, uppercase stages
and task/command arguments, and captures snapshots and richer event metadata. The
validator still requires per-behavior mappings/reviews and refactor/no-refactor
records. These existing constraints require migration as planned in [plan.md](../plan.md);
they are not requirements imposed by constitution v2.0.0. Preserve existing richer
records as supporting evidence without demanding them for future valid increments.

Final order remains `bash scripts/check-quality.sh`,
`.venv/bin/python -m scripts.assemble_evidence`, then
`.venv/bin/python -m scripts.check_evidence`. The quality script records real final
check results; assembly binds them to artifacts and the source/config/test digest.
Validation must preserve final freshness, complete required acceptance identities,
regression, coverage, architecture, static analysis and contract verification while
accepting valid consolidated TDD evidence. Failed/missing mandatory checks must be
reported. Intermediate snapshot requirements are distinct from final-result freshness.

Coverage.py's default ellipsis exclusion applies only to declarative Protocol
signatures; business coverage exclusions remain forbidden. The Waitress typing
suppression stays confined to bootstrap with its existing justification.

## Historical review

`review.json` records a failure under the earlier per-behavior process rule. Its
original observations and execution output remain historical evidence. Grouped Red
suites and coherent grouped implementations alone no longer establish a violation.
Reassess C1/T050 against v2.0.0 using real test commands/results and their chronology;
exclude environmental/import failures as Red and do not infer TDD from final Green.
Record a new evidence-based review decision rather than rewrite historical output
or manufacture failures. This guide does not change review status or certify completion.

## Planned removal boundary

Remove mandatory intermediate snapshot/blob capture, global event-chain continuity,
per-behavior mapping/approval and mandatory refactor/no-refactor records from active
process enforcement. Do not delete their historical outputs. Preserve final-result
hashes/digests for freshness and required scenario identities for acceptance coverage.
An ordinary consolidated execution log plus review context is sufficient when it
honestly demonstrates relevant Red before implementation and Green afterward for
coherent increments. No automated success may substitute for that evidence.
