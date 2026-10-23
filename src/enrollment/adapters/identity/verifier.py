from collections.abc import Callable

from enrollment.application.contracts import IdentityUnavailable
from enrollment.domain.outcomes import InvalidIdentifier
from enrollment.domain.values import SubjectId, VerifiedIdentity


class Verifier:
    def __init__(self, provider: Callable[[str | None], str | None]) -> None:
        self.provider = provider

    def verify(self, credential: str | None) -> VerifiedIdentity | None:
        try:
            subject = self.provider(credential)
        except (RuntimeError, OSError) as exc:
            raise IdentityUnavailable("Identity provider unavailable") from exc
        if subject is None:
            return None
        parsed = SubjectId.create(subject)
        if isinstance(parsed, InvalidIdentifier):
            raise IdentityUnavailable("Invalid identity provider representation")
        return VerifiedIdentity.create(parsed)
