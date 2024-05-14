from typing import Optional

from peewee_async import Manager

from common.dto.user import UserCreateDTO
from common.hasher import Hasher
from common.utils.user import is_student
from infrastructure.database import User
from .abstract_user_repository import AbstractUserRepository


class UserRepository(AbstractUserRepository):
    def __init__(
            self,
            manager: Manager,
            hasher: Hasher
    ):
        self.manager = manager
        self.hasher = hasher

    async def create(self, data: UserCreateDTO) -> User:
        user: User = await self.manager.create(
            User,
            email=data.email,
            hashed_password=self.hasher.get_hash(data.password),
            last_name=data.last_name,
            first_name=data.first_name,
            patronymic=data.patronymic,
            is_student=is_student(data.email)
        )
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

    async def update_password(self, user: User, password: str) -> None:
        user.hashed_password = self.hasher.get_hash(password)
        await self.manager.update(user)
