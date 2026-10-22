# Execution evidence

Use the lightweight recorder from the repository root:

```bash
.venv/bin/python -m scripts.record student-details red .venv/bin/pytest tests/acceptance/test_student_details.py -q
.venv/bin/python -m scripts.record student-details green .venv/bin/pytest tests/acceptance/test_student_details.py -q
```

Execute Red before implementing genuinely missing behavior and Green after the
cohesive increment. Each record retains the actual command, output, exit result and
execution times under `evidence/reconciliation/`. Related behaviors may share an
increment and records may cover several layers. Optional `refactor` or `verification`
runs retain additional results; no separate no-refactor artifact is required.
Do not manufacture failures when behavior already works. Import/constructor/schema
setup/environment failures do not count as behavioral Red. Consider refactoring and
keep relevant tests passing. Passing tests and coverage alone do not establish TDD.

Final sequence:

1. `bash scripts/check-quality.sh` captures all final check results.
2. Review actual new/historical evidence and final results; record the current
   decision separately in `evidence/reconciliation/review.json`.
3. `.venv/bin/python -m scripts.assemble_evidence` hashes/references execution records,
   final checks and current review without approving them.
4. `.venv/bin/python -m scripts.check_evidence` validates freshness, coverage,
   acceptance identities, execution references and review. Any missing/failed check
   prevents completion. Source/test/config changes require final recapture/review.

Constitution IV requires 100% branches for each whole affected business function.
The approved project gate remains stricter: complete Core 100% statement and branch
coverage, including unimported modules; no business exclusions. Default ellipsis
exclusions are permitted only in structurally declarative Protocol modules.

Historical records and original review remain unchanged. `history-index.json` and
`evidence/history/pre-reconciliation/` preserve original final artifact hashes/bytes.
Current review reassesses grouped work under constitution v2.0.0 using actual retained
commands/results, never rewriting history or inferring TDD from final Green.
