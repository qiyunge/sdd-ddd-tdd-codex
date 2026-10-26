# Student enrollment
This project is based on ***Extension_Lab03_GraphQL***, which focuses on implementing GraphQL queries.

**GitHub Repository:** [sdd-ddd-tdd-codex](https://github.com/qiyunge/sdd-ddd-tdd-codex)

Unlike a conventional implementation, this project was developed using **Codex Agent and Spec-Kit**, following a Specification-Driven Development (**SDD**) workflow. Implementation follows the Red → Green → Refactor cycle, with tests driving development against the approved specifications. Implementation follows the Red → Green → Refactor cycle, with tests driving development (TDD) against the approved specifications.

To better explore transaction management, business rules, and concurrency, the implementation focuses on a GraphQL Mutation rather than a business Query. The enrollCourse use case serves as the primary example, demonstrating a complete enrollment workflow involving validation, eligibility checks, persistence, and transactional consistency.

The application is built with Python 3.12, graphql-core, Flask, Waitress, and local SQLite. Its only business endpoint is POST /graphql. The GraphQL schema defines the enrollCourse mutation and includes a placeholder Query root. Prerequisite student, programme, course, and offering data are managed by the host application.

See the GraphQL schema for the API contract.

## Develop and verify

Install [uv](https://docs.astral.sh/uv/), then run from this directory:

```bash
uv sync --frozen --dev --python 3.12
uv run pytest tests/domain tests/application tests/acceptance -q
uv run pytest tests/adapters/test_server.py -q
uv run pytest tests/adapters/test_package_resources.py -q
```

The server test binds an ephemeral loopback port and exercises simultaneous Waitress workers with HTTPX. Other HTTP tests use Flask's test client. Resource validation builds a Hatchling wheel, installs it non-editably in a temporary environment and reads both schemas outside the checkout.

Final verification has three ordered stages. Start without a manifest; the quality stage does not read it:

```bash
bash scripts/check-quality.sh
.venv/bin/python -m scripts.assemble_evidence
.venv/bin/python -m scripts.check_evidence
```

Checks capture raw results first. Review the final state in `specs/001-enroll-course/evidence/reconciliation/v300-review.json` and its active copy `evidence/reconciliation/review.json`. Assembly binds those reviews, required TDD increments, the baseline acceptance inventory and raw results to the source/config/test digest. Validation rejects missing, failed, skipped, tampered or stale evidence. Changing implementation, tests or configuration requires all three stages again. Historical failures are retained. Complete Domain/Application statement and branch coverage must be 100%; architecture, strict mypy, Ruff and Import Linter must pass.

## Host integration

The host supplies a synchronous trusted identity verifier with signature `(credential: str | None) -> str | None`. Return a verified subject string on success or `None` for negative verification. The bridge translates documented `RuntimeError`/`OSError` provider operational faults to identity-unavailable; other programming/contract exceptions propagate to sanitized internal error handling. Wrap provider SDK operational exceptions accordingly. Never derive verification from a caller's target student ID. Missing verifier configuration fails at startup. Deterministic identity callbacks belong only in tests.

Integrate the host's existing verification function with these public factories (replace the host-specific import):

```python
from pathlib import Path
from enrollment.bootstrap import create_app, make_server
from host_identity import verify_subject

app = create_app(Path("/absolute/local/path/enrollment.db"), verify_subject)
make_server(app, host="127.0.0.1", port=8080).run()
```

Use Waitress rather than Flask's development server. Debug is disabled. Provision a database schema explicitly before serving, if needed:

```bash
uv run python -c 'from pathlib import Path; from enrollment.adapters.persistence.sqlite import initialize; initialize(Path("enrollment.db"))'
```

`initialize` creates tables only; it provides no record-management business API. The host must populate prerequisites through its existing processes. Keep the database on a local filesystem with reliable SQLite locking; network filesystems are outside this implementation's verified scope. Each invocation owns a connection, acquires `BEGIN IMMEDIATE` before prerequisite reads and commits explicitly. A lost response never deletes a committed enrollment.

GraphQL rejection and failure types have different reason enums. Alias one field when selecting both in a union:

```graphql
mutation Enroll($input: EnrollCourseInput!) {
  enrollCourse(input: $input) {
    __typename
    ... on EnrollCourseSuccess { studentId courseId }
    ... on EnrollCourseRejected { reason }
    ... on EnrollCourseFailure { failureReason: reason }
  }
}
```

Send JSON `query`, `variables` and optional `operationName`, with opaque credentials in `Authorization`. IDs are exact nonempty strings; GraphQL also applies its standard integer-to-string ID coercion. Expected outcomes return HTTP 200; callers must inspect the union result. See [the validation guide](specs/001-enroll-course/quickstart.md) for rejection precedence, concurrency and fault coverage.

## Required Student details and host integration

Every Student requires nonblank name and email. Email uniqueness compares the entire
supplied address with Unicode `str.casefold()` across all programmes; submitted text
is retained, including significant spaces. StudentEmail equality/hash uses that key;
Student entity identity is StudentId. No email syntax/alias rules are added.

The trusted host can call `enrollment.application.student_details.save_student` with
a dictionary containing `mode` (`create` or `replace`), `student_id`, `programme_id`,
`name`, and `email`, plus a factory returning
`enrollment.adapters.persistence.sqlite.StudentSession(database_path)`. Replacement
supplies the complete record. This operation is not a web endpoint. It returns a
committed `StudentSnapshot(student, saved_version)` or an explicit invalid-input,
existence, outdated-version, email-conflict or technical failure outcome. Read the
current snapshot through `get_student(student_id, sessions)` and supply its raw
`snapshot.saved_version.value` as `expected_version` when replacing. Omitting that
version is invalid input. An outdated replacement changes nothing; deliberately
reload and reconsider the full replacement before retrying. Programming defects
propagate to the host error boundary.

This self-contained example uses a fresh temporary database:

```python
from pathlib import Path
from tempfile import TemporaryDirectory

from enrollment.adapters.persistence.sqlite import StudentSession, initialize
from enrollment.application.student_contracts import StudentSnapshot
from enrollment.application.student_details import get_student, save_student
from enrollment.domain.outcomes import OutdatedVersion

with TemporaryDirectory() as directory:
    database = Path(directory) / "enrollment.db"
    initialize(database)
    sessions = lambda: StudentSession(database)
    details = dict(
        student_id="s", programme_id="p", name="Alex", email="Alex@example.com"
    )
    created = save_student(dict(details, mode="create"), sessions)
    assert isinstance(created, StudentSnapshot)
    assert created.saved_version.value == 1

    snapshot = get_student("s", sessions)
    assert isinstance(snapshot, StudentSnapshot)
    command = dict(
        details,
        mode="replace",
        name="Alex Smith",
        expected_version=snapshot.saved_version.value,
    )
    updated = save_student(command, sessions)
    assert isinstance(updated, StudentSnapshot)
    assert updated.saved_version.value == 2
    assert isinstance(save_student(command, sessions), OutdatedVersion)
```

Snapshot reads finish their transaction and close the connection before returning.
Creation and replacement report success only after commit. If the commit outcome is
uncertain, the host receives `StudentResult.STORAGE_FAILURE`; reconcile through a
later independent `get_student` read. Do not delete or revert a potentially committed
record or automatically replay a replacement against a refreshed version. A lost
response after confirmed commit leaves the committed record intact.

Value Objects use `.create(raw)` for both supplied and stored input when their
validation rules are identical. Invalid input returns `InvalidIdentifier`,
`InvalidStudentDetails`, or `InvalidSavedVersion`; persistence translates these
outcomes into `DataIntegrityFailure` when decoding stored values.
`Programme.create`, `Course.create`, `ProgrammeCourseOffering.create`,
`Enrollment.create`, and `Student.create` accept already validated Domain values.
`VerifiedIdentity.create` accepts a `SubjectId`. Record `.reconstitute` restores
stored rows, including a Student whose programme is not present, and does not replay
offering eligibility or email availability. Persistence maps `InvalidPersistedState`
to `DataIntegrityFailure`, which the use cases report as the existing persistence
failure. Internal constructors remain for misuse detection and are not the supported
construction API.

Use the adapter's `connect` helper for direct provisioning: it registers Domain-backed
SQLite validation/comparison functions. Unconfigured writes fail closed. Initialization
refuses legacy Student schemas without changing their data; hosts must provision a
fresh compatible schema or arrange their own audited migration. No names/emails are
fabricated, and old rows receive no fabricated saved versions. Fresh creation starts
at version 1; every committed replacement, including identical details, advances it
by one. The SQL guard rejects updates without that advancement, but supported edits
still require the conditional host operation and the originally read version.
Compatible initialization is idempotent. Enrollment still cannot write
Student details and its public GraphQL schema/rejection precedence is unchanged.

For validation and lightweight execution recording see
[quickstart](specs/001-enroll-course/quickstart.md) and
[evidence guide](specs/001-enroll-course/evidence/README.md). Final quality capture,
current evidence review, manifest assembly and validation are all required.
