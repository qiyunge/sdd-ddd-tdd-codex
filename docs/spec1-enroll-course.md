# Feature: Student Self-Enrollment

## 1. Business Goal

Allow an existing student to enroll themselves in an existing course offered by their programme.

Successful enrollment must be persisted. Invalid enrollment attempts must be rejected with clear business outcomes.

## 2. Scope

**In scope**
- Student self-enrollment in an existing course.
- Enrollment eligibility, uniqueness, and persistence.
- Rejection of invalid enrollment attempts.

**Out of scope**
- Student, programme, and course management.
- Programme-course offering management.
- Identity verification implementation.
- Withdrawal, capacity, prerequisites, fees, and scheduling.

## 3. Business Rules

1. Each student belongs to one programme. A programme offers multiple courses, and a course may be offered by multiple programmes.
2. Each enrollment associates one student with one course.
3. A student may enroll only themselves. Acting identity must be verified and match the target student identity.
4. Enrollment requires an existing student, programme, and course.
5. A student may enroll only in courses offered by their current programme. Eligibility must hold when enrollment is saved.
6. A student cannot enroll in the same course more than once, including under concurrent requests.
7. Successful enrollment must be persisted before success is reported.
8. Rejected attempts must not create, modify, or delete enrollment records as a consequence of the rejected attempt.
9. Persistence failure must not leave a partial enrollment.
10. Rejections follow **First-match**, without error accumulation, in this order:
    - Unverified acting identity
    - Acting/target identity mismatch
    - Missing student
    - Missing programme
    - Missing course
    - Already enrolled
    - Course not offered by programme

    Identity and ownership failures return generic denial. Other business failures return distinguishable reasons. Dependent checks are skipped when prerequisite records are missing.
11. Retrying after a successfully persisted enrollment must not create another enrollment. When no higher-priority rejection applies, return already enrolled.
