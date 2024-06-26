import logging
from datetime import date, datetime, timedelta
from typing import List, Optional

import peewee
from peewee_async import Manager

from common.dto.reservation import ReservationCreateRequest
from common.exceptions.application import (
    CoworkingNonBusinessDayException,
    NotAllowedReservationTimeException, CoworkingNotExistsException
)
from infrastructure.database import (
    Reservation,
    CoworkingSeat,
    Coworking,
    CoworkingEvent,
    User
)
from infrastructure.database.enum import BookingStatus
from storage.reservation import AbstractReservationRepository

logger = logging.getLogger(__name__)


class ReservationRepository(AbstractReservationRepository):
    def __init__(self, manager: Manager) -> None:
        self.manager = manager

    async def get_user_reservations(self, user: User) -> List[Reservation]:
        query = (
            Reservation.select()
            .where(
                (Reservation.user == user) &
                (Reservation.session_end >= datetime.now()) &
                (Reservation.status != BookingStatus.CANCELLED)
            )
            .join(CoworkingSeat)
            .join(Coworking)
            .order_by(Reservation.session_start.asc())
        )
        return await self.manager.execute(query)

    async def create(
            self,
            user: User,
            reservation: ReservationCreateRequest
    ) -> Reservation:
        await self.check_coworking_exists(reservation.coworking_id)
        await self.check_business_day(reservation.coworking_id,
                                      reservation.session_start.date())
        is_allowed_query = (
            CoworkingSeat.select()
            .where(CoworkingSeat.place_type == reservation.place_type)
            .join(Coworking)
            .where(Coworking.id == reservation.coworking_id)
            .switch(CoworkingSeat)
            .join(Reservation, peewee.JOIN.LEFT_OUTER)
            .where(
                (Reservation.id.is_null()) |
                (Reservation.session_end <= reservation.session_start) |
                (Reservation.session_start >= reservation.session_end) |
                (Reservation.status == BookingStatus.CANCELLED)
            )
        )
        try:
            seat: Optional[CoworkingSeat] = await self.manager.get_or_none(
                is_allowed_query)
        except AttributeError:
            seat = None
        if seat is None:
            raise NotAllowedReservationTimeException()
        status = BookingStatus.NEW
        if (reservation.session_start - datetime.now()) <= timedelta(minutes=30):
            status = BookingStatus.CONFIRMED
        reservation: Reservation = await self.manager.create(
            Reservation,
            user=user,
            seat=seat,
            session_start=reservation.session_start,
            session_end=reservation.session_end,
            status=status
        )
        return reservation

    async def check_coworking_exists(self, coworking_id: str) -> None:
        coworking: Optional[Coworking] = await self.manager.get_or_none(
            Coworking,
            Coworking.id == coworking_id
        )
        if coworking is None:
            raise CoworkingNotExistsException()

    async def check_business_day(self, coworking_id: str, _date: date) -> None:
        event: Optional[CoworkingEvent] = await self.manager.get_or_none(
            CoworkingEvent,
            CoworkingEvent.date == _date,
            coworking_id=coworking_id
        )
        if event is not None:
            raise CoworkingNonBusinessDayException()

    async def mark_as_cancelled(self, reservation: Reservation) -> None:
        reservation.status = BookingStatus.CANCELLED
        await self.manager.update(reservation)

    async def get(self, reservation_id: int) -> Optional[Reservation]:
        try:
            query = (
                Reservation.select(Reservation, User)
                .where(Reservation.id == reservation_id)
                .join(User)
            )
            reservation = await self.manager.get_or_none(query)
            return reservation
        except Exception as exc:
            logger.exception(
                "Failed to fetch Reservation(id=%s) with exc = %s",
                reservation_id, exc
            )
            pass

    async def is_conflict_reservation(
            self,
            user: User,
            session_start: datetime,
            session_end: datetime
    ) -> bool:
        query = (
            Reservation.select()
            .join(User)
            .where(
                (Reservation.user == user) &
                (Reservation.status != BookingStatus.CANCELLED)
            )
            .where(
                ~(
                        (Reservation.session_end <= session_start) |
                        (Reservation.session_start >= session_end)
                )
            )
        )
        result: List[Reservation] = await self.manager.execute(query)
        return len(result) > 0
