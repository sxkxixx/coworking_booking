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
