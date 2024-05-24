from peewee_async import Manager

from common.dto.coworking_event import CoworkingEventSchema
from infrastructure.database import Coworking, CoworkingEvent
from .abstract_coworking_event_repository import AbstractCoworkingEventRepository


class CoworkingEventRepository(AbstractCoworkingEventRepository):
    def __init__(self, manager: Manager):
        self.manager = manager

    async def create(self, coworking: Coworking, event: CoworkingEventSchema) -> CoworkingEvent:
        return await self.manager.create(
            CoworkingEvent,
            coworking=coworking,
            date=event.event_date,
            name=event.name,
            description=event.description,
        )
