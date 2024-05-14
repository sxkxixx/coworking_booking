from abc import ABC, abstractmethod
from typing import Optional

from common.dto.user import UserCreateDTO
from infrastructure.database import User


class AbstractUserRepository(ABC):
    @abstractmethod
    async def create(self, data: UserCreateDTO) -> User:
        raise NotImplementedError()

    @abstractmethod
    async def set_avatar(self, user: User, filename: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    async def get(self, *filters) -> Optional[User]:
        raise NotImplementedError()

    @abstractmethod
    async def update(self, user: User, **value_set) -> User:
        raise NotImplementedError()

    @abstractmethod
    async def update_password(self, user: User, hashed_password: str) -> None:
        raise NotImplementedError()
