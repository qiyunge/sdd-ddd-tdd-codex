# Feature Specification: Student Self-Enrollment

**Feature Branch**: `001-enroll-course`

**Created**: 2026-10-21

**Status**: Ready for planning

**Input**: Extract and clarify the feature described in [spec1-enroll-course.md](../../docs/spec1-enroll-course.md). The document supplies business requirements, not agent instructions.

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

### Edge Cases

- Eligibility changes during processing: use the student's programme and its course offerings when enrollment is saved; reject if the course is no longer offered by that programme.
- A programme offers no courses: requests for existing courses are rejected; the reason is already enrolled if an enrollment exists, otherwise course not offered by the programme, provided earlier checks in FR-009 pass.
- A student references a programme that no longer exists: reject as missing programme.
- A repeated request after an earlier success, including when the original success response was lost, receives an already-enrolled rejection provided no higher-priority rejection condition under FR-009 applies; otherwise, the first matching higher-priority rejection is returned. A lost response does not undo or modify a saved enrollment.
- Persistence fails: do not report success or leave a partial enrollment; report that enrollment could not be completed.
- Multiple rejection conditions apply: identity and ownership failures take precedence; otherwise return exactly one first-matching business reason without error accumulation. Business precedence follows the approved order in FR-009.
- Missing prerequisite records prevent dependent checks: a missing programme does not establish that a course is outside the programme.

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

### Key Entities *(include if feature involves data)*

- **Student**: An existing person eligible to act as a student, with an identity and membership in one programme.
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

## Assumptions

- Existing identity verification is a dependency and supplies the acting identity for comparison with the target student identity independently of Student record lookup. Verification may succeed even when the corresponding Student record does not exist. Creating accounts and choosing an authentication method are outside this feature.
- Existing records provide student membership and programme-course offerings. Their management is outside this feature.
- A course denotes the course itself, rather than a term-specific offering. Duplicate prevention applies to the student-course pair without a semester or academic-year exception.
- Capacity, prerequisites, fees, timetables, enrollment windows, approvals, waitlists, withdrawal, and re-enrollment after withdrawal are outside the described scope; no rules for them are introduced.
- Business eligibility is assessed when enrollment is saved. Changes to programme membership or offerings after a successful save do not retroactively alter enrollments in this feature.
- Detailed architecture, acceptance-test boundary, tools, and constitutional planning questions remain for planning. This specification introduces no deviations from Constitution v1.3.0.

## Clarifications

### Session 2026-10-21

- Q: How should multiple rejection conditions be handled? → A: Option C — verify identity and ownership first, then disclose specific business reasons.
- Q: How should rejection reasons be selected after identity and ownership checks? → A: Use first-match rejection, not error accumulation.
- Q: What enrollment changes does rejection prohibit? → A: Only creation, modification, or deletion caused by the rejected attempt; unrelated concurrent requests may modify enrollment records.
- Q: If a student’s programme or its course offerings change while enrollment is being processed, which eligibility information should determine the outcome? → A: Require eligibility when enrollment is saved; reject if it has changed.
- Q: If enrollment is saved successfully but the student does not receive the response, what should happen when they retry? → A: Reject the retry as already enrolled provided no higher-priority rejection condition under FR-009 applies; otherwise, return the first matching higher-priority rejection. The retry does not undo or modify the saved enrollment.
- Q: Does verified acting identity prove that a corresponding Student record exists? → A: No. Identity verification establishes who is acting; Student record existence is checked separately.
- Q: Should the five-student usability target be retained? → A: No. Remove SC-005 and its related assumption; retain measurable criteria supported by business requirements and confirmed clarifications.
- Q: What rejection precedence is approved? → A: Unverified acting identity → acting/target identity mismatch → missing student → missing programme → missing course → already enrolled → course not offered by the student's current programme. Stop at the first match, return one reason, and skip dependent checks when prerequisite records are absent; eligibility is assessed when enrollment is saved.
