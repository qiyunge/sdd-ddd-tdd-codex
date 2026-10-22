# Student enrollment

Python 3.12 application using graphql-core, Flask, Waitress and local SQLite. The only business endpoint is POST `/graphql`, with the mutation in [the schema](specs/001-enroll-course/contracts/schema.graphqls). Prerequisite student, programme, course and offering data is managed by the host.

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

Checks capture raw results first. Assembly then binds those results and TDD transcripts to the source/config/test digest. Validation rejects missing, failed, skipped, tampered or stale evidence. Review notes live in `specs/001-enroll-course/evidence/review.json`; changing implementation, tests or configuration requires all three stages again. Historical failures are retained. Complete Domain/Application statement and branch coverage must be 100%; architecture, strict mypy, Ruff and Import Linter must pass.

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
committed Student or an explicit invalid-input, existence, email-conflict or technical
failure outcome. Programming defects propagate to the host error boundary.

Use the adapter's `connect` helper for direct provisioning: it registers Domain-backed
SQLite validation/comparison functions. Unconfigured writes fail closed. Initialization
refuses legacy Student schemas without changing their data; hosts must provision a
fresh compatible schema or arrange their own audited migration. No names/emails are
fabricated. Compatible initialization is idempotent. Enrollment still cannot write
Student details and its public GraphQL schema/rejection precedence is unchanged.

For validation and lightweight execution recording see
[quickstart](specs/001-enroll-course/quickstart.md) and
[evidence guide](specs/001-enroll-course/evidence/README.md). Final quality capture,
current evidence review, manifest assembly and validation are all required.
