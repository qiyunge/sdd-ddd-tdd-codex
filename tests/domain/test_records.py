import pytest

from enrollment.domain.models import (
    Course,
    Enrollment,
    Programme,
    ProgrammeCourseOffering,
    Student,
)
from enrollment.domain.values import CourseId, ProgrammeId, StudentId


@pytest.mark.parametrize(
    "kind,args",
    [
        (Student, ("s", ProgrammeId("p"))),
        (Student, (StudentId("s"), "p")),
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


def test_valid_records():
    s = Student(StudentId("s"), ProgrammeId("missing"))
    assert s.programme_id.value == "missing"
    assert Programme(ProgrammeId("p")).programme_id.value == "p"
    assert Course(CourseId("c")).course_id.value == "c"
    assert ProgrammeCourseOffering(
        ProgrammeId("p"), CourseId("c")
    ).course_id == CourseId("c")
    assert Enrollment(StudentId("s"), CourseId("c")) == Enrollment(
        StudentId("s"), CourseId("c")
    )
