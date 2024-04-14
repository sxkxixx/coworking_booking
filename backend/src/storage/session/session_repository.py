from abc import ABC, abstractmethod
from datetime import timedelta
from typing import Optional

from common.session.session import Session


class SessionRepository(ABC):
    @abstractmethod
    async def setex(self, entity: Session) -> str:
        raise NotImplementedError()

    @abstractmethod
    async def get(self, key) -> Optional[Session]:
        raise NotImplementedError()

    @property
    @abstractmethod
    def session_ttl(self) -> timedelta:
        raise NotImplementedError()

    @abstractmethod
    async def delete(self, session_id) -> None:
        raise NotImplementedError()
