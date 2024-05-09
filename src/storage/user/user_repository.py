from typing import Optional

from peewee_async import Manager

from infrastructure.database import User
from .abstract_user_repository import AbstractUserRepository


class UserRepository(AbstractUserRepository):
    def __init__(self, manager: Manager):
        self.manager = manager

    async def create(self, **kwargs) -> User:
        user: User = await self.manager.create(User, **kwargs)
        return user

    async def get(self, *filters) -> Optional[User]:
        user: Optional[User] = await self.manager.get_or_none(User, *filters)
        return user

    async def set_avatar(self, user: User, filename: str) -> None:
        await self.manager.execute(
            User.update({User.avatar_filename: filename})
            .where(User.id == user.id)
        )

    async def update(self, user: User, **value_set) -> User:
        updated = await self.manager.update(user, value_set)
        return await self.manager.get(User, User.id == user.id)
