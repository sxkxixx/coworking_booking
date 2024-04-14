import os
from datetime import timedelta
from typing import Optional

from aioredis import Redis

from common.session.session import Session
from .session_repository import SessionRepository


class RedisSessionRepository(SessionRepository):
    def __init__(
            self,
            redis: Redis,
            session_ttl: timedelta
    ):
        self.__redis: Redis = redis
        self.__session_ttl = session_ttl

    async def setex(self, entity: Session) -> str:
        session_id = self.__get_random_id()
        await self.__redis.setex(session_id, self.__session_ttl, entity.model_dump_json())
        return session_id

    async def get(self, key: str) -> Optional[Session]:
        session = await self.__redis.get(key)
        if not session:
            return None
        return Session.model_validate_json(session)

    @property
    def session_ttl(self):
        return self.session_ttl

    @staticmethod
    def __get_random_id() -> str:
        return os.urandom(24).hex()

    async def delete(self, session_id: str) -> None:
        await self.__redis.delete(session_id)
