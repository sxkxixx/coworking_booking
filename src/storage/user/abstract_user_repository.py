from abc import ABC, abstractmethod
from typing import Optional

from infrastructure.database import User, UserTelegramInfo


class AbstractUserRepository(ABC):
    @abstractmethod
    async def create(self, **kwargs) -> User:
        raise NotImplementedError()

    @abstractmethod
    async def set_avatar(self, user: User, filename: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    async def get(self, *filters) -> Optional[User]:
        raise NotImplementedError()

    @abstractmethod
    async def get_user_telegram_info(self, user_id: str) -> Optional[UserTelegramInfo]:
        raise NotImplementedError()

    @abstractmethod
    async def update(self, user: User, **value_set) -> User:
        raise NotImplementedError()
