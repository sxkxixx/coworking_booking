from typing import List, Optional

import fastapi_jsonrpc as jsonrpc

from common.context import CONTEXT_USER
from common.dto.reservation import ReservationResponse, ReservationCreateRequest
from common.exceptions.application import (
    CoworkingNonBusinessDayException,
    NotAllowedReservationTimeException,
    CoworkingNotExistsException
)
from common.exceptions.rpc import UnauthorizedError, ReservationException
from infrastructure.database import User, Reservation
from storage.reservation import AbstractReservationRepository
from .abstract_rpc_router import AbstractRPCRouter


class ReservationRouter(AbstractRPCRouter):
    def __init__(self, reservation_repository: AbstractReservationRepository):
        self.reservation_repository = reservation_repository

    def build_entrypoint(self) -> jsonrpc.Entrypoint:
        entrypoint = jsonrpc.Entrypoint(
            path='/api/v1/reservation',
            tags=['RESERVATION'],
            errors=[UnauthorizedError]
        )
        entrypoint.add_method_route(self.get_user_reservations)
        entrypoint.add_method_route(self.create_reservation, errors=[ReservationException])
        entrypoint.add_method_route(self.cancel_reservation, errors=[ReservationException])
        return entrypoint

    async def get_user_reservations(self) -> List[ReservationResponse]:
        user: Optional[User] = CONTEXT_USER.get()
        if not user:
            raise UnauthorizedError()
        reservations: List[Reservation] = await self.reservation_repository.get_user_reservations(
            user_id=user.id)
        response_data = [
            ReservationResponse.model_validate(reservation, from_attributes=True)
            for reservation in reservations
        ]
        return response_data

    async def create_reservation(
            self, reservation: ReservationCreateRequest
    ) -> ReservationResponse:
        user: Optional[User] = CONTEXT_USER.get()
        if not user:
            raise UnauthorizedError()
        try:
            created = await self.reservation_repository.create(user.id, reservation)
        except CoworkingNotExistsException:
            raise ReservationException(data={'error': 'coworking does not exists'})
        except CoworkingNonBusinessDayException:
            raise ReservationException(data={'error': 'coworking does not work this date'})
        except NotAllowedReservationTimeException:
            raise ReservationException(
                data={'error': 'not allowed to create a reservation to this timestamp range'}
            )
        return ReservationResponse.model_validate(created, from_attributes=True)

    async def cancel_reservation(
            self,
            reservation_id: int,
    ) -> None:
        user: Optional[User] = CONTEXT_USER.get()
        if not user:
            raise UnauthorizedError()
        reservation: Optional[Reservation] = await self.reservation_repository.get(reservation_id)
        if not reservation:
            raise ReservationException(data={'error': 'reservation does not exist'})
        if reservation.user != user:
            raise ReservationException(
                data={'error': 'unable to cancel another user reservation'}
            )
        await self.reservation_repository.mark_as_cancelled(reservation)
        return None
