from datetime import date
from typing import List, Optional

import peewee
from peewee_async import Manager

from common.dto.reservation import ReservationCreateRequest
from common.exceptions.application import (
    CoworkingNonBusinessDayException,
    NotAllowedReservationTimeException
)
from infrastructure.database import Reservation, CoworkingSeat, Coworking, NonBusinessDay, User
from storage.reservation import AbstractReservationRepository


class ReservationRepository(AbstractReservationRepository):
    def __init__(self, manager: Manager) -> None:
        self.manager = manager

    async def get_user_reservation(self, user_id) -> List[Reservation]:
        query = (
            Reservation.select()
            .where(
                (Reservation.user.id == user_id) &
                (Reservation.session_start.date() >= date.today())
            )
            .join(CoworkingSeat)
            .join(Coworking)
            .order_by(Reservation.session_start.asc())
        )
        return await self.manager.execute(query)

    async def create(self, user: User, reservation: ReservationCreateRequest) -> Reservation:
        is_business_day: Optional[NonBusinessDay] = await self.manager.get_or_none(
            NonBusinessDay,
            NonBusinessDay.coworking.id == reservation.coworking_id,
            NonBusinessDay.day == reservation.session_start.date()
        )
        if is_business_day is not None:
            raise CoworkingNonBusinessDayException()
        is_allowed_query = (
            Coworking.select()
            .where(Coworking.id == reservation.coworking_id)
            .join(CoworkingSeat, peewee.JOIN.LEFT_OUTER)
            .where(CoworkingSeat.place_type.value == reservation.place_type.value)
            .join(Reservation, peewee.JOIN.LEFT_OUTER)
            .where(
                (Reservation.id.is_null()) |
                (Reservation.session_end <= reservation.session_start) |
                (Reservation.session_start >= reservation.session_end)
            )
        )
        coworking: Optional[Coworking] = await self.manager.get_or_none(is_allowed_query)
        if coworking is None:
            raise NotAllowedReservationTimeException()
        coworking_seat: CoworkingSeat = coworking.seats[0]
        reservation: Reservation = await self.manager.create(
            Reservation,
            user=user,
            seat=coworking_seat,
            session_start=reservation.session_start,
            session_end=reservation.session_end
        )
        return reservation
