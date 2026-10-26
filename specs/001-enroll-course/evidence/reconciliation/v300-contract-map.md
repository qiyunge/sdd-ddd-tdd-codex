# v3.0.0 lifecycle review map

Review sources: [Repository lifecycle](../../contracts/repository-lifecycle.md),
[Domain construction](../../contracts/domain-construction.md),
[enrollment](../../contracts/enrollment-api.md), and
[Student details](../../contracts/student-details.md).

| Boundary | Required returned state/outcome | Review obligation |
|---|---|---|
| Enrollment Repository create | pending Enrollment, PairConflict or Domain rejection | INSERT acknowledged, actual composite identity, Domain factory before enclosing commit |
| Prerequisite Repository | pending Programme/Course/Offering or restored Entity/None | stored identity before factory; restoration avoids current admission policy |
| Student create | pending StudentSnapshot, AlreadyExists, EmailKeyConflict or Domain rejection | explicit version 1, INSERT confirmation, whole-operation rollback on rejection |
| Student replacement | pending snapshot, NotFound, VersionConflict, EmailKeyConflict or transition rejection | confirmed identity, controlled transition, full identity+version guarded write |
| Snapshot read | detached StudentSnapshot, NotFound or technical failure | same-row details/version; validate version even for enrollment-only reads |
| Input/policy | InvalidIdentifier, InvalidStudentDetails, InvalidSavedVersion, OutdatedVersion, EmailConflict | IDs/details/mode/version before lookup; existence before version; stale before email |
| Known active uncommitted | rollback entire UoW, discard pending Entity | Repository never commits; no callbacks/caches/exception payloads containing pending results |
| Confirmed commit | external success permitted after close | one enclosing commit; no later deletion/reversion after response/cleanup fault |
| Uncertain commit | StorageFailure and independent reconciliation | no inferred success, destructive compensation or automatic Student write replay |
| Cleanup fault over ordinary result | StorageFailure | retain diagnostic context, never ordinary rejection with unconfirmed termination |
| Primary programming exception | original exception plus cleanup diagnostics | unexpected faults never become business outcomes |
| Corrupt state/schema | DataIntegrityFailure/StorageFailure | no fabricated migration/default versions; no ordinary missing/input outcome |

Enrollment replay is one fresh complete ordered attempt after PairConflict, then a
technical failure if unresolved. Student stale replacement has no replay. Pending
results remain operation-local; no Entity lifetime handles or reservation tables.
