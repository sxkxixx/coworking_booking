from abc import ABC, abstractmethod
from typing import Optional

from infrastructure.database import User


class AbstractUserRepository(ABC):
    @abstractmethod
    async def create(self, **kwargs) -> User:
        raise NotImplementedError()

    @abstractmethod
    async def get(self, *filters) -> Optional[User]:
        raise NotImplementedError()

    @abstractmethod
    async def set_avatar(self, user: User, filename: str) -> None:
        raise NotImplementedError()
