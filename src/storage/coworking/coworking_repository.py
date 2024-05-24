from datetime import date, datetime
from typing import Optional, List

import peewee
from peewee_async import Manager

from common.dto.coworking import CoworkingCreateDTO
from common.dto.input_params import SearchParams, TimestampRange
from common.dto.tech_capability import TechCapabilitySchema
from infrastructure.database import (
    Coworking,
    CoworkingSeat,
    WorkingSchedule,
    CoworkingImages,
    CoworkingEvent,
    Reservation,
    TechCapability
)
from infrastructure.database.enum import BookingStatus
from .abstract_coworking_repository import AbstractCoworkingRepository


class CoworkingRepository(AbstractCoworkingRepository):
    def __init__(self, manager: Manager):
        self.manager = manager

    async def get_coworking_by_id(self, coworking_id: str) -> Optional[Coworking]:
        try:
            return await self.manager.get_or_none(
                Coworking.select()
                .where(Coworking.id == coworking_id)
                .join(CoworkingSeat, peewee.JOIN.LEFT_OUTER)
                .switch(Coworking).join(WorkingSchedule, peewee.JOIN.LEFT_OUTER)
                .switch(Coworking).join(CoworkingImages, peewee.JOIN.LEFT_OUTER)
                .switch(Coworking).join(CoworkingEvent, peewee.JOIN.LEFT_OUTER)
                .where((CoworkingEvent.id.is_null()) | (date.today() <= CoworkingEvent.date))
                .switch(Coworking).join(TechCapability, peewee.JOIN.LEFT_OUTER)
            )
        except AttributeError:
            return None

    async def find_by_search_params(self, search_params: SearchParams) -> List[Coworking]:
        not_null_filter_dict = search_params.model_dump(exclude_none=True)
        query = Coworking.select()
        for attr, value in not_null_filter_dict.items():
            query = query.where(getattr(Coworking, attr) == value)
        # query = query.join(CoworkingImages, peewee.JOIN.LEFT_OUTER)
        return await self.manager.execute(query)

    async def select_filter_by_timestamp_range(self, interval: TimestampRange) -> List[Coworking]:
        query = (
            Coworking.select().distinct()
            # Фильтрация по времени работы коворкинга
            .join(WorkingSchedule, peewee.JOIN.LEFT_OUTER)
            .where(
                (WorkingSchedule.id.is_null()) |
                (
                        (WorkingSchedule.week_day == interval.start.weekday()) &
                        (WorkingSchedule.start_time <= interval.start.time()) &
                        (interval.end.time() <= WorkingSchedule.end_time)
                )
            )
            # Проверка, работает ли коворкинг в указанный день
            .switch(Coworking)
            .join(CoworkingEvent, peewee.JOIN.LEFT_OUTER)
            .where(
                (CoworkingEvent.date.is_null()) |
                (CoworkingEvent.date != interval.start.date())
            )
            # Проверка, есть ли доступное свободное место в указанное время
            .switch(Coworking)
            .join(CoworkingSeat, peewee.JOIN.LEFT_OUTER)
            .join(Reservation, peewee.JOIN.LEFT_OUTER)
            .where(
                (Reservation.id.is_null()) |
                (Reservation.status == BookingStatus.CANCELLED) |
                (Reservation.session_end <= interval.start) |
                (Reservation.session_start >= interval.end)
            )
        )
        return await self.manager.execute(query)

    async def get(self, coworking_id: str) -> Optional[Coworking]:
        coworking = await self.manager.get_or_none(Coworking, Coworking.id == coworking_id)
        return coworking

    async def create_coworking(self, dto: CoworkingCreateDTO) -> Coworking:
        return await self.manager.create(Coworking, **dto.model_dump())

    async def set_avatar_filename(self, coworking: Coworking, avatar_image_filename: str) -> None:
        coworking.avatar = avatar_image_filename
        await self.manager.update(coworking)

    async def create_coworking_image(self, coworking: Coworking, filename: str) -> None:
        await self.manager.create(CoworkingImages, coworking=coworking, image_filename=filename)

    async def create_tech_capabilities(
            self,
            coworking: Coworking,
            capabilities: List[TechCapabilitySchema]
    ) -> List[TechCapability]:
        result = []
        async with self.manager.transaction():
            for capability in capabilities:
                created = await self.manager.create(
                    TechCapability,
                    coworking=coworking,
                    capability=capability.capability
                )
                result.append(created)
        return result

    async def get_coworking_schedule_at_day(self, d: date | datetime) -> Optional[WorkingSchedule]:
        return await self.manager.get_or_none(
            WorkingSchedule,
            WorkingSchedule.week_day == d.weekday()
        )
