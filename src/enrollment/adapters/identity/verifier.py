from collections.abc import Callable

from enrollment.application.contracts import IdentityUnavailable
from enrollment.domain.values import SubjectId, VerifiedIdentity


class Verifier:
    def __init__(self, provider: Callable[[str | None], str | None]) -> None:
        self.provider = provider

    def verify(self, credential: str | None) -> VerifiedIdentity | None:
        try:
            subject = self.provider(credential)
            return None if subject is None else VerifiedIdentity(SubjectId(subject))
        except Exception as exc:
            raise IdentityUnavailable("Identity provider unavailable") from exc
