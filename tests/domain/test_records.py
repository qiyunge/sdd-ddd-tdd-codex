"""Domain rules only: valid supplied IDs here do not prove persistence confirmation.

Model constraints:
Programme: Valid confirmed identity; existing prerequisite, no management use case added.
Course: Valid confirmed identity; shared by multiple programmes.
Offering: Both confirmed typed components; represents a persisted offering relationship.
Enrollment: Unique confirmed pair; new admission requires approved prerequisite/duplicate/offering policy sequence.
"""

import pytest

from enrollment.domain.models import (
    Course,
    Enrollment,
    Programme,
    ProgrammeCourseOffering,
    Student,
)
from enrollment.domain.outcomes import InvalidPersistedState
from enrollment.domain.values import (
    CourseId,
    ProgrammeId,
    StudentEmail,
    StudentId,
    StudentName,
)


@pytest.mark.parametrize(
    "kind,args",
    [
        (
            Student,
            (
                "s",
                ProgrammeId("p"),
                StudentName("Alex"),
                StudentEmail("alex@example.com"),
            ),
        ),
        (
            Student,
            (
                StudentId("s"),
                "p",
                StudentName("Alex"),
                StudentEmail("alex@example.com"),
            ),
        ),
        (Programme, ("p",)),
        (Course, ("c",)),
        (ProgrammeCourseOffering, ("p", CourseId("c"))),
        (ProgrammeCourseOffering, (ProgrammeId("p"), "c")),
        (Enrollment, ("s", CourseId("c"))),
        (Enrollment, (StudentId("s"), "c")),
    ],
)
def test_invalid_reconstitution(kind, args):
    with pytest.raises(ValueError):
        kind(*args)


def test_factories_reconstitute_without_replaying_context():
    programme = Programme.create(ProgrammeId("p"))
    assert programme == Programme.reconstitute(ProgrammeId("p"))
    with pytest.raises(ValueError):
        Programme.create("p")
    assert isinstance(Programme.reconstitute("p"), InvalidPersistedState)
    course = Course.create(CourseId("c"))
    assert course == Course.reconstitute(CourseId("c"))
    with pytest.raises(ValueError):
        Course.create("c")
    assert isinstance(Course.reconstitute("c"), InvalidPersistedState)
    offering = ProgrammeCourseOffering.create(ProgrammeId("p"), CourseId("c"))
    assert offering == ProgrammeCourseOffering.reconstitute(
        ProgrammeId("p"), CourseId("c")
    )
    with pytest.raises(ValueError):
        ProgrammeCourseOffering.create("p", CourseId("c"))
    with pytest.raises(ValueError):
        ProgrammeCourseOffering.create(ProgrammeId("p"), "c")
    assert isinstance(
        ProgrammeCourseOffering.reconstitute(ProgrammeId("p"), "c"),
        InvalidPersistedState,
    )
    dangling = Student.reconstitute(
        StudentId("s"),
        ProgrammeId("missing"),
        StudentName("Alex"),
        StudentEmail("alex@example.com"),
    )
    assert dangling.programme_id.value == "missing"


def test_valid_records():
    s = Student.create(
        StudentId("s"),
        ProgrammeId("missing"),
        StudentName("Alex"),
        StudentEmail("alex@example.com"),
    )
    assert s.programme_id.value == "missing"
    assert Programme.create(ProgrammeId("p")).programme_id.value == "p"
    assert Course.create(CourseId("c")).course_id.value == "c"
    assert ProgrammeCourseOffering.create(
        ProgrammeId("p"), CourseId("c")
    ).course_id == CourseId("c")
    assert Enrollment.create(StudentId("s"), CourseId("c")) == Enrollment.create(
        StudentId("s"), CourseId("c")
    )


def test_controlled_student_transition_preserves_identity_and_exact_text():
    original = Student.create(
        StudentId.create("s"),
        ProgrammeId.create("p"),
        StudentName.create("Alex"),
        StudentEmail.create("Alex@Example.com"),
    )
    changed = original.replace_details(
        ProgrammeId.create("dangling"),
        StudentName.create(" New "),
        StudentEmail.create("aLEX@EXAMPLE.COM"),
    )
    assert changed.student_id is original.student_id
    assert changed == original and hash(changed) == hash(original)
    assert changed.name.value == " New " and changed.email.value == "aLEX@EXAMPLE.COM"
    assert original.name.value == "Alex"
    for args in [
        ("bad", changed.name, changed.email),
        (changed.programme_id, "bad", changed.email),
        (changed.programme_id, changed.name, "bad"),
    ]:
        with pytest.raises(ValueError):
            original.replace_details(*args)
