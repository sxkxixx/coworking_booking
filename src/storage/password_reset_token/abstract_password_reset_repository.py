from abc import ABC, abstractmethod
from typing import Optional

from infrastructure.database import User
from infrastructure.database.models import PasswordResetToken


class AbstractPasswordResetTokenRepository(ABC):
    @abstractmethod
    async def create(self, user: User, fingerprint: str) -> PasswordResetToken:
        raise NotImplementedError()

    @abstractmethod
    async def get(self, *filters) -> Optional[PasswordResetToken]:
        raise NotImplementedError()

    @abstractmethod
    async def mark_token_as_used(self, token: PasswordResetToken) -> None:
        raise NotImplementedError()
