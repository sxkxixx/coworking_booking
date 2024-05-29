from abc import ABC, abstractmethod
from datetime import date
from typing import Optional, List

from common.dto.coworking import CoworkingCreateDTO
from common.dto.coworking_seat import CreateSeatDTO
from common.dto.input_params import SearchParams, TimestampRange
from common.dto.schedule import ScheduleCreateDTO
from common.dto.tech_capability import TechCapabilitySchema
from infrastructure.database import Coworking, TechCapability, WorkingSchedule


class AbstractCoworkingRepository(ABC):
    @abstractmethod
    async def get_coworking_by_id(self, coworking_id: str) -> Optional[Coworking]:
        raise NotImplementedError()

    @abstractmethod
    async def find_by_search_params(self, search_params: SearchParams) -> List[Coworking]:
        raise NotImplementedError()

    @abstractmethod
    async def select_filter_by_timestamp_range(self, interval: TimestampRange) -> List[Coworking]:
        raise NotImplementedError()

    @abstractmethod
    async def create_coworking(self, dto: CoworkingCreateDTO) -> Coworking:
        raise NotImplementedError()

    @abstractmethod
    async def get(self, coworking_id: str) -> Optional[Coworking]:
        raise NotImplementedError()

    @abstractmethod
    async def set_avatar_filename(self, coworking: Coworking, avatar_image_filename: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    async def create_coworking_image(self, coworking: Coworking, filename: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    async def create_tech_capabilities(
            self,
            coworking: Coworking,
            capabilities: List[TechCapabilitySchema]
    ) -> List[TechCapability]:
        raise NotImplementedError()

    @abstractmethod
    async def get_coworking_schedule_at_day(self, d: date) -> Optional[WorkingSchedule]:
        raise NotImplementedError()

    @abstractmethod
    async def register_schedule(
            self,
            coworking: Coworking,
            schedules: List[ScheduleCreateDTO]
    ) -> List[WorkingSchedule]:
        raise NotImplementedError()

    @abstractmethod
    async def create_places(
            self,
            coworking: Coworking,
            table_places: int,
            meeting_rooms: List[CreateSeatDTO]
    ):
        raise NotImplementedError()
