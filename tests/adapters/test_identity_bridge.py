import pytest

from enrollment.adapters.identity.verifier import Verifier
from enrollment.application.contracts import IdentityUnavailable
from enrollment.domain.values import SubjectId, VerifiedIdentity


def test_trusted():
    assert Verifier(lambda c: "s").verify("opaque") == VerifiedIdentity(SubjectId("s"))
    assert Verifier(lambda c: None).verify(None) is None


def test_provider_failure():
    def down(c):
        raise RuntimeError("secret")

    with pytest.raises(IdentityUnavailable):
        Verifier(down).verify("opaque")


def test_invalid_provider_identity():
    with pytest.raises(IdentityUnavailable):
        Verifier(lambda c: "").verify("opaque")
