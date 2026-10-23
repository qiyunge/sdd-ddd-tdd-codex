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
