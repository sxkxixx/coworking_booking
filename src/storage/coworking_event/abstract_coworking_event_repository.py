from abc import ABC, abstractmethod

from common.dto.coworking_event import CoworkingEventSchema
from infrastructure.database import Coworking, CoworkingEvent


class AbstractCoworkingEventRepository(ABC):
    @abstractmethod
    async def create(self, coworking: Coworking, event: CoworkingEventSchema) -> CoworkingEvent:
        raise NotImplementedError()
