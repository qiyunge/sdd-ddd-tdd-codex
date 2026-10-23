import pytest

from enrollment.domain.models import Enrollment, Student
from enrollment.domain.outcomes import InvalidPersistedState, InvalidStudentDetails
from enrollment.domain.values import (
    CourseId,
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
    assert kind.create(" Alex ").value == " Alex "


def test_value_equality_and_identity():
    a, b = StudentEmail("Straße@Example.com"), StudentEmail("STRASSE@EXAMPLE.COM")
    assert a == b and b == a and not (a != b)
    assert hash(a) == hash(b) and len({a, b}) == 1 and {a: "value"}[b] == "value"
    assert a != StudentEmail("other@example.com")
    assert a.__eq__("Straße@Example.com") is NotImplemented
    assert a != StudentName("Straße@Example.com")
    first = Student.create(StudentId("s"), ProgrammeId("p"), StudentName("First"), a)
    changed = Student.create(
        StudentId("s"), ProgrammeId("other"), StudentName("Changed"), b
    )
    assert first == changed and hash(first) == hash(changed)
    assert first != Student.create(
        StudentId("other"), ProgrammeId("p"), StudentName("First"), a
    )
    assert first.__eq__("s") is NotImplemented
    with pytest.raises(ValueError):
        Student(StudentId("s"), ProgrammeId("p"), "invalid", a)


def test_typed_student_create_and_reconstitution():
    student = Student.create(
        StudentId("s"), ProgrammeId("p"), StudentName("Alex"), StudentEmail("a@b.co")
    )
    assert student == Student.reconstitute(
        StudentId("s"), ProgrammeId("p"), StudentName("Alex"), StudentEmail("a@b.co")
    )
    with pytest.raises(ValueError):
        Student.create(
            "s", ProgrammeId("p"), StudentName("Alex"), StudentEmail("a@b.co")
        )
    with pytest.raises(ValueError):
        Student.create(StudentId("s"), "p", StudentName("Alex"), StudentEmail("a@b.co"))
    with pytest.raises(ValueError):
        Student.create(StudentId("s"), ProgrammeId("p"), "Alex", StudentEmail("a@b.co"))
    with pytest.raises(ValueError):
        Student.create(StudentId("s"), ProgrammeId("p"), StudentName("Alex"), "a@b.co")
    name = StudentName("Alex")
    email = StudentEmail("a@b.co")
    assert isinstance(
        Student.reconstitute("s", ProgrammeId("p"), name, email), InvalidPersistedState
    )
    assert isinstance(
        Student.reconstitute(StudentId("s"), "p", name, email), InvalidPersistedState
    )
    assert isinstance(
        Student.reconstitute(StudentId("s"), ProgrammeId("p"), "Alex", email),
        InvalidPersistedState,
    )
    assert isinstance(
        Student.reconstitute(StudentId("s"), ProgrammeId("p"), name, "a@b.co"),
        InvalidPersistedState,
    )
    enrollment = Enrollment.create(StudentId("s"), CourseId("c"))
    assert enrollment == Enrollment.reconstitute(StudentId("s"), CourseId("c"))
    with pytest.raises(ValueError):
        Enrollment.create("s", CourseId("c"))
    with pytest.raises(ValueError):
        Enrollment.create(StudentId("s"), "c")
    assert isinstance(Enrollment.reconstitute("", CourseId("c")), InvalidPersistedState)
    assert isinstance(
        Enrollment.reconstitute(StudentId("s"), ""), InvalidPersistedState
    )


def test_email_composition_is_not_normalized():
    composed = StudentEmail("caf\u00e9@example.com")
    decomposed = StudentEmail("cafe\u0301@example.com")
    assert composed != decomposed
    assert len({composed, decomposed}) == 2
    assert composed.value == "caf\u00e9@example.com"
    assert decomposed.value == "cafe\u0301@example.com"


@pytest.mark.parametrize(
    "raw", [None, True, False, "1", 1.0, 0, -1, 9223372036854775808]
)
def test_saved_version_rejects_unusable_input(raw):
    from enrollment.domain import outcomes, values

    assert hasattr(values, "SavedVersion"), "Saved version is a required Domain value"
    assert isinstance(values.SavedVersion.create(raw), outcomes.InvalidSavedVersion)
    with pytest.raises(ValueError):
        values.SavedVersion(raw)


@pytest.mark.parametrize("raw", [1, 9223372036854775807])
def test_saved_version_boundaries(raw):
    from enrollment.domain.values import SavedVersion

    assert SavedVersion.create(raw).value == raw
