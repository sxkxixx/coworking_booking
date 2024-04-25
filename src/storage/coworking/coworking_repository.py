from typing import Optional, List

import peewee
from peewee_async import Manager

from common.dto.input_params import SearchParams, TimestampRange
from infrastructure.database import (
    Coworking,
    CoworkingSeat,
    WorkingSchedule,
    CoworkingImages,
    NonBusinessDay,
    Reservation
)
from .abstract_coworking_repository import AbstractCoworkingRepository


class CoworkingRepository(AbstractCoworkingRepository):
    def __init__(self, manager: Manager):
        self.manager = manager

    async def get_coworking_by_id(self, coworking_id: str) -> Optional[Coworking]:
        coworking = await self.manager.get_or_none(
            Coworking.select(Coworking)
            .where(Coworking.id == coworking_id)
            .join(CoworkingSeat, peewee.JOIN.LEFT_OUTER)
            .switch(Coworking)
            .join(WorkingSchedule, peewee.JOIN.LEFT_OUTER)
            .switch(Coworking)
            .join(CoworkingImages, peewee.JOIN.LEFT_OUTER)
        )
        return coworking

    async def find_by_search_params(self, search_params: SearchParams) -> List[Coworking]:
        not_null_filter_dict = search_params.model_dump(exclude_none=True)
        query = Coworking.select()
        for attr, value in not_null_filter_dict.items():
            query = query.where(getattr(Coworking, attr) == value)
        # query = query.join(CoworkingImages, peewee.JOIN.LEFT_OUTER)
        return await self.manager.execute(query)

    async def select_filter_by_timestamp_range(self, interval: TimestampRange) -> List[Coworking]:
        query = (
            Coworking.select()
            # Фильтрация по времени работы коворкинга
            .join(WorkingSchedule, peewee.JOIN.LEFT_OUTER)
            .where(WorkingSchedule.week_day == interval.start.weekday())
            .where(
                (WorkingSchedule.start_time <= interval.start) &
                (interval.end <= WorkingSchedule.end_time)
            )
            # Проверка, работает ли коворкинг в указанный день
            .switch(Coworking)
            .join(NonBusinessDay, peewee.JOIN.LEFT_OUTER)
            .where(
                (NonBusinessDay.day.is_null(True)) |
                (NonBusinessDay.day != interval.start.date())
            )
            # Проверка, есть ли доступное свободное место в указанное время
            .switch(Coworking)
            .join(CoworkingSeat, peewee.JOIN.LEFT_OUTER)
            .join(Reservation, peewee.JOIN.LEFT_OUTER)
            .where(
                (Reservation.id.is_null(True)) |
                (
                        (Reservation.session_end <= interval.start) |
                        (Reservation.session_start >= interval.end)
                )

            )
        )
        return await self.manager.execute(query)
