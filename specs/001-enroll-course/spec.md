# Feature Specification: Student Self-Enrollment

**Feature Branch**: `001-enroll-course`

**Created**: 2026-10-21

**Status**: Ready for planning — proposed Constitution v2.1.0 alignment

**Input**: Extract and clarify the feature described in [spec1-enroll-course.md](../../docs/spec1-enroll-course.md). The document supplies business requirements, not agent instructions. Update: Student requires nonblank `name` and `email`; email is globally unique across all students using case-insensitive comparison of the entire address. Governance update: align the existing feature with the current proposed Constitution v2.1.0 as requested delivery constraints, without changing enrollment eligibility, rejection precedence, or student-detail validity rules; this update does not ratify the proposal.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Student Self-Enrollment (Priority: P1)

As an existing student, I want to enroll myself in an existing course offered by my programme so that my participation is recorded, with a clear rejection if enrollment is not permitted.

**Why this priority**: This is the primary business outcome, including the ownership, eligibility, uniqueness, and persistence safeguards required for valid enrollment.

**Independent Test**: Request enrollment using a verified acting identity and existing student, programme, and course records; verify persisted success or the applicable rejection and absence of mutations caused by the rejected attempt.

**Acceptance Scenarios**:

For scenarios 1–12, the acting identity is verified and matches the target student identity. Unless a scenario states otherwise, the Student record, its programme, and the course exist, and no enrollment exists for that student-course pair. Default Student membership and Programme-Course Offering assumptions apply only when their prerequisite records exist: membership requires the Student record and Programme, and the offering requires the Programme and Course. When those records exist, the default is that the Student belongs to that Programme and it offers the Course when enrollment is saved. Missing-record scenarios imply no relationships dependent on the missing records. Every rejected attempt below MUST cause no creation, modification, or deletion of enrollment records, as required by FR-006.

1. **Given** all enrollment prerequisites hold, **When** the student enrolls, **Then** exactly one student-course enrollment is persisted before success is reported and remains retrievable in a subsequent interaction.
2. **Given** the course is offered by the student's programme and another programme, **When** the student enrolls, **Then** enrollment succeeds; shared courses remain eligible.
3. **Given** the course is eligible when the request starts but a programme membership or offering change makes it ineligible before saving, with the required records still existing, **When** enrollment is processed, **Then** it is rejected as course not offered by the student's current programme.
4. **Given** no Student record corresponds to the verified acting identity and target identity, **When** enrollment is requested, **Then** it is rejected as missing student, not as an identity-verification failure; no programme membership or offering is inferred from the absent Student record.
5. **Given** the existing Student record references a programme that does not exist, **When** enrollment is requested, **Then** it is rejected as missing programme; no course-offering conclusion is inferred from the absent programme.
6. **Given** the requested course does not exist, **When** enrollment is requested, **Then** it is rejected as missing course; course-offering eligibility is not inferred from the absent course.
7. **Given** the existing course is not offered by the student's existing programme, **When** enrollment is requested, **Then** it is rejected as course not offered by the student's programme.
8. **Given** an enrollment already exists for the student-course pair, **When** enrollment is requested again, **Then** it is rejected as already enrolled and that attempt leaves the existing enrollment unchanged.
9. **Given** enrollment was saved successfully but its success response was lost, **When** the student retries, **Then** the retry is rejected as already enrolled provided no higher-priority rejection condition under FR-009 applies; otherwise, the first matching higher-priority rejection is returned. The retry does not undo or change the saved enrollment.
10. **Given** two eligible requests for the same student-course pair arrive concurrently with no prior enrollment, **When** both requests finish processing, **Then** exactly one succeeds, the other is rejected as already enrolled, and exactly one enrollment exists.
11. **Given** an otherwise valid enrollment cannot be persisted, **When** enrollment is processed, **Then** failure rather than success is reported and no partially created enrollment remains.
12. **Given** the student is already enrolled in an existing course that is not offered by their current programme, with all prerequisite records existing, **When** enrollment is requested, **Then** only the already-enrolled rejection is returned under FR-009; the programme-course eligibility check is not evaluated and no rejection reasons are accumulated.
13. **Given** no verified acting identity is available, **When** enrollment is requested, **Then** only a generic denial is returned without disclosing student, programme, course, or enrollment information, regardless of any other failures.
14. **Given** the verified acting identity differs from the target student identity, **When** enrollment is requested, **Then** only a generic denial is returned without disclosing student, programme, course, or enrollment information, regardless of any other failures.
15. **Given** an invalid attempt and an unrelated valid enrollment request run concurrently, **When** both complete, **Then** the invalid attempt causes no enrollment mutations and the unrelated valid request succeeds and persists its enrollment, provided persistence is available and its prerequisites remain valid.

### User Story 2 - Valid Student Details (Priority: P1)

As a student, I want my record to include a name and an email that no other student uses so that my details are complete and my email distinguishes me from other students.

**Why this priority**: These are required invariants of every Student used by enrollment.

**Independent Test**: Establish, restore, and change student details independently of enrollment; check required text and email uniqueness across programmes, including concurrent attempts.

**Acceptance Scenarios**:

1. **Given** name and email each contain a non-whitespace character and the email is unused by other students ignoring case, **When** student details are established, **Then** both attributes are accepted and retained.
2. **Given** either attribute is missing, empty, or whitespace-only (including spaces, tabs, and line breaks), **When** a Student is created, restored from saved records, or changed, **Then** no invalid Student is accepted as valid; normal creation or changes return an invalid-input rejection and a rejected change preserves previous details, while invalid saved details encountered during restoration are reported as a data-integrity failure rather than a user-input or business rejection.
3. **Given** a student uses `Alex@Example.com`, **When** another student in any programme is assigned `Alex@Example.com`, `alex@Example.com`, `Alex@example.COM`, or `aLEX@EXAMPLE.COM`, **Then** each attempt is rejected as an email conflict and existing details remain unchanged. The same rule applies beyond ASCII: `Straße@example.com` and `STRASSE@EXAMPLE.COM` conflict under full Unicode case folding, including its multi-character expansions.
4. **Given** a student uses `Alex@Example.com`, **When** another student is assigned `alex+other@example.com` or `alex@other.example`, **Then** uniqueness permits the address because the entire addresses remain different after full Unicode case folding. Leading/trailing whitespace remains significant. Given `café@example.com` with precomposed `é` (U+00E9), assigning `café@example.com` with `e` followed by a combining acute accent (U+0065 U+0301) to another student succeeds and retains both original addresses, because Unicode composition forms are not made equivalent.
5. **Given** a student has a unique email, **When** that student retains it or changes only its case, **Then** uniqueness does not reject the address as a conflict with themselves.
6. **Given** two different students concurrently claim the same unused email with or without case differences, **When** both attempts finish, **Then** exactly one succeeds, the other receives an email-conflict rejection, and no duplicate is retained.
7. **Given** valid existing student details, **When** they are changed to a nonblank name and an email unused by other students, **Then** the change succeeds; changing to another student's email is rejected and preserves previous details.

### Edge Cases

- Eligibility changes during processing: use the student's programme and its course offerings when enrollment is saved; reject if the course is no longer offered by that programme.
- A programme offers no courses: requests for existing courses are rejected; the reason is already enrolled if an enrollment exists, otherwise course not offered by the programme, provided earlier checks in FR-009 pass.
- A student references a programme that no longer exists: reject as missing programme.
- A repeated request after an earlier success, including when the original success response was lost, receives an already-enrolled rejection provided no higher-priority rejection condition under FR-009 applies; otherwise, the first matching higher-priority rejection is returned. A lost response does not undo or modify a saved enrollment.
- Persistence fails: do not report success or leave a partial enrollment; report that enrollment could not be completed. Invalid saved state encountered during restoration is a data-integrity failure, not a missing record, user-input validation failure, or ordinary business rejection; it does not introduce a new rejection step in FR-009.
- Multiple rejection conditions apply: identity and ownership failures take precedence; otherwise return exactly one first-matching business reason without error accumulation. Business precedence follows the approved order in FR-009.
- Missing prerequisite records prevent dependent checks: a missing programme does not establish that a course is outside the programme.

- Whitespace-only names and emails include tabs and line breaks, not just spaces.
- Email conflicts apply across programmes and to case differences in either the local part or domain. Names need not be unique.
- Retaining one's own email, including a case-only change, causes no self-conflict. Concurrent claims by different students cannot produce duplicates.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST accept enrollment only for a verified acting identity targeting its own student identity. Identity verification establishes who is acting; it MUST NOT be treated as proof that a corresponding Student record exists. The system MUST deny requests without a verified acting identity and reject requests targeting a different identity. Student record existence MUST be checked separately under FR-002 and FR-009.
- **FR-002**: Enrollment MUST require an existing target student, that student's existing programme, and an existing target course.
- **FR-003**: The target course MUST be offered by the student's current programme when enrollment is saved. Eligibility at request start alone MUST NOT permit enrollment if programme membership or course offerings change before saving. If the current programme no longer offers the course, the system MUST reject enrollment and cause no creation, modification, or deletion of enrollment records; the rejection reason is course not offered by the student's programme when selected under FR-009. Being offered by additional programmes MUST NOT make it ineligible.
- **FR-004**: A successful enrollment MUST associate exactly one student with exactly one course and MUST be persisted before success is reported.
- **FR-005**: At most one enrollment MUST exist for each student-course pair, including under concurrent requests. Further attempts MUST be rejected, including retries after a successful save whose response was lost; the reason MUST be already enrolled when no higher-priority rejection condition under FR-009 applies. Otherwise, the first matching higher-priority rejection MUST be returned. The saved enrollment MUST remain unchanged; a lost response MUST NOT undo it.
- **FR-006 — Rejection Side Effects**: A rejected enrollment attempt MUST NOT create, modify, or delete enrollment records as a consequence of that attempt. This restriction MUST NOT prevent unrelated concurrent requests from modifying enrollment records.
- **FR-007**: After acting identity and self-ownership are verified, the system MUST return explicit, distinguishable business rejection reasons: missing student, missing programme, missing course, course not offered by the student's programme, or already enrolled. Identity or ownership failures MUST receive the generic denial specified in FR-009.
- **FR-008**: If an enrollment cannot be persisted, the system MUST report failure rather than success and MUST leave no partially created enrollment.
- **FR-009 — First-Match Rejection**: The system MUST evaluate enrollment rejection conditions in the following precedence order:

  1. Unverified acting identity
  2. Acting identity does not match the target student identity
  3. Missing student
  4. Missing programme
  5. Missing course
  6. Already enrolled
  7. Course not offered by the student's current programme

  The system MUST stop at the first matching rejection condition and return exactly one rejection reason. Identity verification and ownership failures MUST return a generic denial without disclosing student, programme, course, or enrollment information. After identity and ownership verification, business rejection reasons MUST be explicit and distinguishable. The system MUST NOT accumulate rejection reasons. Dependent checks MUST NOT be evaluated when their prerequisite records do not exist: the student's programme cannot be determined without a Student record, and programme-course eligibility requires the Student record, its programme, and the course. In particular, missing prerequisite records MUST NOT be interpreted as failed programme-course eligibility. When reached, eligibility MUST be evaluated against the student's current programme and its course offerings when enrollment is saved, consistent with FR-003.

- **FR-010**: Enrollment MUST NOT create or modify students, programmes, courses, programme membership, or programme-course offerings.

- **FR-011 — Required Student Details**: Every Student MUST have text attributes `name` and `email`, each containing at least one non-whitespace character. Missing, empty, or whitespace-only values MUST be rejected during creation, restoration from saved records, and changes. Invalid details MUST NOT be accepted as a valid Student. During restoration, invalid saved details MUST be reported as a data-integrity failure rather than a user-input validation failure or ordinary business rejection.
- **FR-012 — Global Email Uniqueness**: No two different students may have equal email addresses under full Unicode caseless comparison of the entire address, regardless of programme. Equality MUST be determined by full Unicode case folding of both the local part and domain, including multi-character expansions: `Straße@example.com` and `STRASSE@EXAMPLE.COM` MUST conflict. The system MUST NOT add Unicode composition normalization, whitespace removal, or provider-specific alias, dot, or plus-tag equivalence. Original supplied spelling MUST be retained. Retaining one's own email or changing only its case MUST NOT cause a self-conflict. Uniqueness MUST hold under concurrent attempts.
- **FR-013 — Student Detail Rejections**: During normal creation or changes, invalid required text and an email assigned to another student MUST produce distinguishable rejection reasons. Restoration failures follow the data-integrity classification in FR-011. Rejected creation MUST create no Student; rejected changes MUST preserve previous details. These invariants MUST NOT add enrollment rejection steps or change FR-009 precedence. Enrollment MUST continue to use existing valid Student records without modifying them under FR-010.

### Key Entities *(include if feature involves data)*

- **Student**: An existing person eligible to act as a student, with an identity, membership in one programme, a required nonblank `name`, and a required nonblank `email` globally unique across all students under case-insensitive comparison of the entire address. Each text attribute must contain at least one non-whitespace character; names need not be unique.
- **Programme**: An existing programme to which a student belongs; it may offer multiple courses.
- **Course**: An existing course that may be offered by multiple programmes.
- **Programme Course Offering**: The existing relationship establishing that a programme offers a particular course.
- **Enrollment**: The persisted association of one student with one course; the student-course pair is unique.
- **Acting Identity**: The verified identity initiating enrollment, used to establish who is acting and compare the acting and target identities. A verified acting identity may have no corresponding Student record; matching identities establish self-ownership, not Student record existence.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every eligible self-enrollment acceptance example produces exactly one enrollment that remains retrievable in a subsequent interaction.
- **SC-002**: Every invalid acceptance example causes no creation, modification, or deletion of enrollment records by the rejected attempt and returns exactly one first-matching rejection under FR-009. Unrelated concurrent requests may still modify enrollment records.
- **SC-003**: For two simultaneous eligible requests for the same student-course pair, exactly one succeeds and exactly one enrollment remains.
- **SC-004**: Every business rejection category disclosed after ownership verification is distinguishable in single-failure acceptance examples, enabling a student or reviewer to identify the reason without consulting internal diagnostics.

- **SC-005**: Every student-detail acceptance example rejects missing, empty, or whitespace-only required text and accepts otherwise valid details with a unique email; zero invalid Students are accepted as valid, and invalid saved details encountered during restoration are classified as data-integrity failures rather than input or business rejections.
- **SC-006**: All exact and Unicode case-fold-equivalent email conflicts (including `Straße@example.com` versus `STRASSE@EXAMPLE.COM`) across different students and programmes are rejected; the composed/decomposed addresses in US2 scenario 4 are both accepted and retained unchanged; for two concurrent claims to one unused address, exactly one succeeds and zero duplicates remain.
- **SC-007**: Every rejected student-detail change preserves previous details, and users can distinguish invalid text from an email conflict without internal diagnostics.

## Assumptions

- Existing identity verification is a dependency and supplies the acting identity for comparison with the target student identity independently of Student record lookup. Verification may succeed even when the corresponding Student record does not exist. Creating accounts and choosing an authentication method are outside this feature.
- Student-detail requirements define record validity; no student-management interface is added and enrollment cannot create or edit students. Existing saved records must satisfy these invariants; a data-cleanup or migration workflow is outside this specification.
- This update adds no email syntax validation, ownership verification, automatic trimming, or provider-specific normalization. Beyond rejecting whitespace-only text, uniqueness compares the complete supplied text using full Unicode case folding, including multi-character expansions, without removing whitespace or normalizing Unicode composition. This makes `Straße@example.com` conflict with `STRASSE@EXAMPLE.COM` while preserving the original supplied spelling.
- Existing records provide student membership and programme-course offerings. Their management is outside this feature.
- A course denotes the course itself, rather than a term-specific offering. Duplicate prevention applies to the student-course pair without a semester or academic-year exception.
- Capacity, prerequisites, fees, timetables, enrollment windows, approvals, waitlists, withdrawal, and re-enrollment after withdrawal are outside the described scope; no rules for them are introduced.
- Business eligibility is assessed when enrollment is saved. Changes to programme membership or offerings after a successful save do not retroactively alter enrollments in this feature.
- Constitution v2.0.0 remains the last historically recorded ratified baseline. At the user's direction, this feature targets the current proposed v2.1.0 construction, validation, and verification contracts as delivery constraints. This specification does not ratify v2.1.0 or represent it as effective project-wide policy. Enrollment eligibility, FR-009 rejection precedence, student-detail validity, and existing measurable business outcomes remain unchanged; restoration failure classification is clarified above.
- Domain exclusively owns business decisions, state transitions, and invariants. Application coordinates use-case-level validation, authorization, and business orchestration. Adapters may parse and validate external representations and directly use supported Domain factories or reconstitution for technical boundary adaptation; Application is not a mandatory gateway. Adapters must not duplicate Domain business rules or orchestrate use cases. Inward dependencies and Full Bridge isolation apply without redundant validation, DTOs, or mappings solely for layering.
- All Value Objects and Entities require consistent, explicit factories for normal creation, including Entities without additional cross-field constraints. Entity factories accept validated Domain Types and enforce applicable entity-level invariants. Expected validation and business creation failures return explicit outcomes. Internal constructors are not supported public creation alternatives; internal misuse may raise contract exceptions, and absolute language-level constructor privacy is not required.
- Persistence reconstitution is a separate, allowed controlled Domain operation callable directly by Persistence Adapters implementing Core-owned Ports. It enforces persisted-state invariants without reapplying creation-only eligibility. Invalid persisted state is a data-integrity failure, whose representation and propagation are defined by the shared error contract, rather than an ordinary input or business rejection.
- Delivery MUST follow acceptance-guided Outside-In TDD in cohesive behavioral increments. Each increment requires execution of a relevant behavioral test that fails for the expected reason before implementation, implementation of the required behavior with relevant tests passing, and consideration of refactoring with relevant tests remaining passing. Related behaviors MAY share an increment; separate cycles per assertion, branch, or independently testable behavior are not required. Refactoring need not change code when none is warranted.
- Automated tests MUST verify responsibilities in every affected layer and MAY exercise multiple layers through a shared behavioral boundary. Lightweight Red and Green evidence MUST identify relevant implementation states and execution order sufficiently to review test-first chronology. Test output without state or revision association is not conclusive proof. Evidence MUST distinguish acceptance-first verification from subsequent inner-layer TDD activity where performed. Consolidation is permitted if behavioral increments and chronology remain identifiable; no commit per cycle, exhaustive logs, intermediate source snapshots, or separate no-refactor artifacts are required. Storage, retention, and state-association mechanisms remain shared project-level decisions.
- Final acceptance and regression tests, whole-affected-function or method 100% business-logic branch coverage, architecture fitness tests, static analysis, and contract verification remain mandatory against the final implementation state. Architecture verification MUST distinguish automated structural checks from behavioral contract tests or explicit review; dependency checks alone do not verify semantic boundary isolation. Passing tests and coverage alone do not prove TDD compliance.
- Planning MUST apply established shared architectural conventions, construction/error contracts, testing tools, and evidence policies rather than independently redefine them. Plans specify feature-level acceptance boundaries, transaction coordination, concrete boundary contracts, environments, and implementation mechanisms within shared policy. Unresolved shared decisions block only implementation that depends on them; unrelated work may proceed.
- This requirements-level alignment does not establish implementation or historical TDD compliance. Tasks record C1/T050 reassessment under v2.0.0 and subsequent verification; those historical outcomes are preserved, not automatically invalidated or accepted as proof of v2.1.0 alignment. Existing plan, tasks, and verification/evidence mechanisms require review against these delivery constraints before new implementation or completion claims. Missing historical evidence must be reported honestly rather than manufactured.


## Clarifications

### Session 2026-10-21

- Q: How should multiple rejection conditions be handled? → A: Option C — verify identity and ownership first, then disclose specific business reasons.
- Q: How should rejection reasons be selected after identity and ownership checks? → A: Use first-match rejection, not error accumulation.
- Q: What enrollment changes does rejection prohibit? → A: Only creation, modification, or deletion caused by the rejected attempt; unrelated concurrent requests may modify enrollment records.
- Q: If a student’s programme or its course offerings change while enrollment is being processed, which eligibility information should determine the outcome? → A: Require eligibility when enrollment is saved; reject if it has changed.
- Q: If enrollment is saved successfully but the student does not receive the response, what should happen when they retry? → A: Reject the retry as already enrolled provided no higher-priority rejection condition under FR-009 applies; otherwise, return the first matching higher-priority rejection. The retry does not undo or modify the saved enrollment.
- Q: Does verified acting identity prove that a corresponding Student record exists? → A: No. Identity verification establishes who is acting; Student record existence is checked separately.
- Q: Should the five-student usability target be retained? → A: No. The removed SC-005 referred to the obsolete five-student usability target and its related assumption. It does not refer to the current Student Details SC-005, which remains approved and unchanged; retain measurable criteria supported by business requirements and confirmed clarifications.
- Q: What rejection precedence is approved? → A: Unverified acting identity → acting/target identity mismatch → missing student → missing programme → missing course → already enrolled → course not offered by the student's current programme. Stop at the first match, return one reason, and skip dependent checks when prerequisite records are absent; eligibility is assessed when enrollment is saved.

- Update: Student requires nonblank `name` and `email`; the entire email is globally unique across all students ignoring case. User Story 2, FR-011–FR-013, and SC-005–SC-007 define this extension.

### Session 2026-10-22

- Refinement: FR-012 uses full Unicode caseless matching of the whole email address, including multi-character case-fold expansions such as `ß` to `ss`. Original spelling is retained; whitespace removal, Unicode composition normalization, and provider-specific equivalences remain excluded. This makes the existing plan and task semantics explicit in the business requirements.

- Constitution alignment: adopted the current proposed v2.1.0 contracts as feature delivery constraints without ratifying them. Enrollment eligibility, rejection precedence, email comparison, and validity rules are unchanged. US2 scenario 2, FR-011/FR-013, and SC-005 distinguish invalid saved state from normal input rejection. Historical C1/T050 status is referenced as recorded in tasks rather than described as still incomplete. Planning must assess construction, reconstitution, semantic-boundary verification, and state-associated TDD evidence under shared project decisions.
