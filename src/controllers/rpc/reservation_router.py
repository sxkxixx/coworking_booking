from typing import List, Optional

import fastapi_jsonrpc as jsonrpc

from common.context import CONTEXT_USER
from common.dto.reservation import ReservationResponse, ReservationCreateRequest
from common.exceptions.application import CoworkingNonBusinessDayException, \
    NotAllowedReservationTimeException
from common.exceptions.rpc import Unauthorized
from infrastructure.database import User, Coworking
from storage.reservation import AbstractReservationRepository
from .abstract_rpc_router import AbstractRPCRouter


class ReservationRouter(AbstractRPCRouter):
    def __init__(self, reservation_repository: AbstractReservationRepository):
        self.reservation_repository = reservation_repository

    def build_entrypoint(self) -> jsonrpc.Entrypoint:
        entrypoint = jsonrpc.Entrypoint(path='/api/v1/reservation', tags=['RESERVATION'])
        entrypoint.add_method_route(self.get_user_reservations)
        entrypoint.add_method_route(self.create_reservation)
        return entrypoint

    async def get_user_reservations(self) -> List[ReservationResponse]:
        user: Optional[User] = CONTEXT_USER.get()
        if not user:
            raise Unauthorized()
        reservations: List[Coworking] = await self.reservation_repository.get_user_reservation(
            user_id=user.id
        )
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
            raise Unauthorized()
        try:
            created = await self.reservation_repository.create(user.id, reservation)
        except CoworkingNonBusinessDayException:
            raise
        except NotAllowedReservationTimeException:
            raise
        return ReservationResponse.model_validate(created, from_attributes=True)
