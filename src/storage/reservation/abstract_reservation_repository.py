from abc import ABC, abstractmethod
from typing import List

from common.dto.reservation import ReservationCreateRequest
from infrastructure.database import Reservation


class AbstractReservationRepository(ABC):
    @abstractmethod
    async def get_user_reservation(self, user_id) -> List[Reservation]:
        raise NotImplementedError()

    @abstractmethod
    async def create(self, user_id: str, reservation: ReservationCreateRequest) -> Reservation:
        raise NotImplementedError()
