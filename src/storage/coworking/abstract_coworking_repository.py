from abc import ABC, abstractmethod
from typing import Optional, List

from common.dto.input_params import SearchParams, TimestampRange
from infrastructure.database import Coworking


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
