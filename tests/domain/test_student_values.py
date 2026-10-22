import pytest

from enrollment.domain.models import Enrollment, Student
from enrollment.domain.outcomes import InvalidIdentifier, InvalidStudentDetails
from enrollment.domain.values import (
    ProgrammeId,
    StudentEmail,
    StudentId,
    StudentName,
)


@pytest.mark.parametrize("kind", [StudentName, StudentEmail])
@pytest.mark.parametrize("bad", [None, 3, "", " \t\n", "\u00a0"])
def test_text_guards_and_outcomes(kind, bad):
    with pytest.raises(ValueError):
        kind(bad)
    assert isinstance(kind.create(bad), InvalidStudentDetails)


def test_value_equality_and_identity():
    a, b = StudentEmail("Straße@Example.com"), StudentEmail("STRASSE@EXAMPLE.COM")
    assert a == b and b == a and not (a != b)
    assert hash(a) == hash(b) and len({a, b}) == 1 and {a: "value"}[b] == "value"
    assert a != StudentEmail("other@example.com")
    assert a.__eq__("Straße@Example.com") is NotImplemented
    assert a != StudentName("Straße@Example.com")
    first = Student(StudentId("s"), ProgrammeId("p"), StudentName("First"), a)
    changed = Student(StudentId("s"), ProgrammeId("other"), StudentName("Changed"), b)
    assert first == changed and hash(first) == hash(changed)
    assert first != Student(
        StudentId("other"), ProgrammeId("p"), StudentName("First"), a
    )
    assert first.__eq__("s") is NotImplemented
    with pytest.raises(ValueError):
        Student(StudentId("s"), ProgrammeId("p"), "invalid", a)


def test_record_factories_return_expected_failures():
    factory = getattr(Student, "create", lambda *args: None)
    assert isinstance(factory("s", "p", " ", "valid"), InvalidStudentDetails), (
        "Student factory must reject raw invalid details with a returned outcome"
    )
    assert isinstance(factory("", "p", "Alex", "valid"), InvalidIdentifier)
    assert isinstance(factory("s", "", "Alex", "valid"), InvalidIdentifier)
    assert isinstance(factory("s", "p", "Alex", ""), InvalidStudentDetails)
    assert isinstance(factory("s", "p", "Alex", "valid"), Student)
    factory = getattr(Enrollment, "create", lambda *args: None)
    assert isinstance(factory("", "c"), InvalidIdentifier)
    assert isinstance(factory("s", ""), InvalidIdentifier)
    assert isinstance(factory("s", "c"), Enrollment)
