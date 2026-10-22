"""Expected port outcomes and unexpected failures remain distinct."""

import pytest

from enrollment.adapters.identity.verifier import Verifier as ProviderVerifier
from enrollment.application import contracts
from enrollment.application.contracts import Command, Failure
from enrollment.application.enroll import enroll
from tests.application.test_enrollment_flow import FlowSession
from tests.application.test_identity import Verifier


def test_returned_pair_conflict_replays_full_order():
    class First(FlowSession):
        def add(self, value):
            self.calls.append("add")
            return getattr(contracts, "PairConflict", "PAIR_CONFLICT")

    first = First()
    second = FlowSession(existing=True)
    sessions = iter([first, second])
    result = enroll(Command("s", "c", "s"), Verifier("s"), lambda: next(sessions))
    assert result == "ALREADY_ENROLLED", (
        "returned pair conflict must trigger ordered replay"
    )
    assert "commit" not in first.calls
    assert first.calls[-1] == "close"


def test_provider_programming_error_is_not_an_outage():
    def defective(credential):
        raise AssertionError("programming defect")

    with pytest.raises(AssertionError, match="programming defect"):
        ProviderVerifier(defective).verify("s")


def test_invalid_input_uses_result_factory(monkeypatch):
    from enrollment.domain.values import StudentId

    def forbidden(self, raw):
        raise AssertionError("invalid input must not reach constructor")

    monkeypatch.setattr(StudentId, "__init__", forbidden)
    assert (
        enroll(Command("", "c", "s"), Verifier("s"), lambda: None)
        == Failure.INVALID_REQUEST
    )


def test_cleanup_does_not_mask_programming_failure():
    class Broken(FlowSession):
        def student(self, identity):
            raise AssertionError("primary defect")

        def close(self):
            raise contracts.StorageFailure("cleanup defect")

    with pytest.raises(AssertionError, match="primary defect"):
        enroll(Command("s", "c", "s"), Verifier("s"), Broken)
