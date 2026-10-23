"""StudentId, ProgrammeId, CourseId and SubjectId are exact nonempty strings; whitespace is not trimmed and case is not folded.

These isolated Domain tests establish invariants, not persistence confirmation.
"""

from dataclasses import FrozenInstanceError

import pytest

from enrollment.domain.outcomes import InvalidIdentifier
from enrollment.domain.values import (
    CourseId,
    ProgrammeId,
    StudentId,
    SubjectId,
    VerifiedIdentity,
)


@pytest.mark.parametrize("kind", [StudentId, ProgrammeId, CourseId, SubjectId])
@pytest.mark.parametrize("bad", [None, 1, ""])
def test_invalid(kind, bad):
    with pytest.raises(ValueError):
        kind(bad)


@pytest.mark.parametrize("kind", [StudentId, ProgrammeId, CourseId, SubjectId])
def test_exact_immutable(kind):
    v = kind(" A ")
    assert v.value == " A "
    with pytest.raises(FrozenInstanceError):
        v.value = "b"


def test_distinct_and_trusted():
    assert StudentId("a") != CourseId("a")
    assert VerifiedIdentity.create(SubjectId("a")).subject_id == SubjectId("a")
    with pytest.raises(ValueError):
        VerifiedIdentity("a")
    with pytest.raises(ValueError):
        VerifiedIdentity.create("a")


@pytest.mark.parametrize("kind", [StudentId, ProgrammeId, CourseId, SubjectId])
@pytest.mark.parametrize("bad", [None, 1, ""])
def test_factory_rejects_unusable_identifiers(kind, bad):
    assert isinstance(kind.create(bad), InvalidIdentifier)
    created = kind.create(" A ")
    assert isinstance(created, kind) and created.value == " A "
