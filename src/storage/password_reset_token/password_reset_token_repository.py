from typing import Optional

import peewee_async

from infrastructure.database import User, PasswordResetToken
from infrastructure.database.enum import PasswordTokenEnum
from .abstract_password_reset_repository import AbstractPasswordResetTokenRepository


class PasswordResetTokenRepository(AbstractPasswordResetTokenRepository):
    def __init__(self, manager: peewee_async.Manager):
        self.manager = manager

    async def create(self, user: User, fingerprint: str) -> PasswordResetToken:
        return await self.manager.create(PasswordResetToken, user=user, fingerprint=fingerprint)

    async def get(self, token: str, email: str) -> Optional[PasswordResetToken]:
        query = (
            PasswordResetToken.select()
            .where(
                (PasswordResetToken.id == token) &
                (PasswordResetToken.status == PasswordTokenEnum.NEW)
            )
            .join(User)
            .where(User.email == email)
        )
        try:
            return await self.manager.get_or_none(query)
        except AttributeError:
            return None

    async def mark_token_as_used(self, token: PasswordResetToken) -> None:
        token.status = PasswordTokenEnum.USED
        await self.manager.update(token)
