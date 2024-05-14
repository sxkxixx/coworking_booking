from abc import ABC, abstractmethod
from typing import List, Optional

from common.dto.reservation import ReservationCreateRequest
from infrastructure.database import Reservation


class AbstractReservationRepository(ABC):
    @abstractmethod
    async def get_user_reservations(self, user_id) -> List[Reservation]:
        raise NotImplementedError()

    @abstractmethod
    async def create(self, user_id: str, reservation: ReservationCreateRequest) -> Reservation:
        raise NotImplementedError()

    @abstractmethod
    async def mark_as_cancelled(self, reservation: Reservation) -> None:
        raise NotImplementedError()

    @abstractmethod
    async def get(self, reservation_id: int) -> Optional[Reservation]:
        raise NotImplementedError()
