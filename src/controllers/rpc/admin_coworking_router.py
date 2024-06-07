import http
from typing import List, Optional

import fastapi_jsonrpc as jsonrpc
from fastapi import UploadFile, File, HTTPException

from common.context import CONTEXT_USER
from common.dto.coworking import CoworkingCreateDTO, CoworkingResponseDTO
from common.dto.coworking_event import CoworkingEventSchema, CoworkingEventResponseSchema
from common.dto.coworking_seat import CoworkingSeatResponse, CreateSeatDTO
from common.dto.schedule import ScheduleCreateDTO, ScheduleResponseDTO
from common.dto.tech_capability import TechCapabilitySchema
from common.exceptions.rpc import (
    CoworkingDoesNotExistException,
    UnauthorizedError,
    NotAdminException
)
from common.utils.image_validators import is_valid_image_signature
from infrastructure.database import Coworking, TechCapability, CoworkingEvent, CoworkingSeat, User
from storage.coworking import AbstractCoworkingRepository
from storage.coworking_event import AbstractCoworkingEventRepository
from storage.s3_repository import S3Repository
from .abstract_rpc_router import AbstractRPCRouter


class AdminCoworkingRouter(AbstractRPCRouter):
    def __init__(
            self,
            coworking_repository: AbstractCoworkingRepository,
            coworking_event_repository: AbstractCoworkingEventRepository,
            s3_repository: S3Repository
    ):
        self.coworking_event_repository = coworking_event_repository
        self.coworking_repository = coworking_repository
        self.s3_repository = s3_repository

    def build_entrypoint(self) -> jsonrpc.Entrypoint:
        entrypoint = jsonrpc.Entrypoint(
            path="/api/v1/admin/coworking",
            tags=["ADMIN COWORKING"],
            errors=[UnauthorizedError, NotAdminException]
        )
        entrypoint.add_method_route(self.create_coworking)
        entrypoint.add_method_route(
            self.create_coworking_tech_capabilities, errors=[CoworkingDoesNotExistException]
        )
        entrypoint.add_method_route(
            self.create_coworking_event, errors=[CoworkingDoesNotExistException]
        )
        entrypoint.add_method_route(
            self.register_coworking_working_schedule, errors=[CoworkingDoesNotExistException]
        )
        entrypoint.add_method_route(
            self.register_coworking_seats, errors=[CoworkingDoesNotExistException]
        )
        entrypoint.add_api_route(
            "/api/v1/admin/coworking/avatar", self.upload_coworking_avatar, methods=["POST"],
            tags=["ADMIN COWORKING REST"]
        )
        entrypoint.add_api_route(
            "/api/v1/admin/coworking/image", self.add_coworking_image, methods=["POST"],
            tags=["ADMIN COWORKING REST"]
        )
        return entrypoint

    async def create_coworking(self, coworking: CoworkingCreateDTO) -> CoworkingResponseDTO:
        self.__check_admin()
        coworking: Coworking = await self.coworking_repository.create_coworking(coworking)
        return CoworkingResponseDTO.model_validate(coworking, from_attributes=True)

    async def upload_coworking_avatar(
            self,
            coworking_id: str,
            image: UploadFile = File()
    ) -> str:
        self.__check_admin()
        if not await is_valid_image_signature(image):
            raise HTTPException(
                status_code=http.HTTPStatus.BAD_REQUEST,
                detail="Invalid image signature"
            )
        coworking: Optional[Coworking] = await self.coworking_repository.get(coworking_id)
        if not coworking:
            raise HTTPException(status_code=http.HTTPStatus.NOT_FOUND.value)
        avatar_image_filename = await self.s3_repository.upload_file(image)
        await self.coworking_repository.set_avatar_filename(coworking, avatar_image_filename)
        return avatar_image_filename

    async def add_coworking_image(
            self,
            coworking_id: str,
            image: UploadFile = File(),
    ) -> str:
        self.__check_admin()
        if not await is_valid_image_signature(image):
            raise HTTPException(
                status_code=http.HTTPStatus.BAD_REQUEST,
                detail="Invalid image signature"
            )
        coworking: Optional[Coworking] = await self.coworking_repository.get(coworking_id)
        if not coworking:
            raise HTTPException(status_code=http.HTTPStatus.NOT_FOUND.value)
        image_filename = await self.s3_repository.upload_file(image)
        await self.coworking_repository.create_coworking_image(coworking, image_filename)
        return image_filename

    async def create_coworking_tech_capabilities(
            self,
            coworking_id: str,
            capabilities: List[TechCapabilitySchema]
    ) -> List[TechCapabilitySchema]:
        self.__check_admin()
        coworking: Optional[Coworking] = await self.coworking_repository.get(coworking_id)
        if not coworking:
            raise CoworkingDoesNotExistException()
        capabilities: List[TechCapability] = (
            await self.coworking_repository.create_tech_capabilities(coworking, capabilities)
        )
        return [
            TechCapabilitySchema.model_validate(item, from_attributes=True)
            for item in capabilities
        ]

    async def create_coworking_event(
            self,
            coworking_id: str,
            event: CoworkingEventSchema
    ) -> CoworkingEventResponseSchema:
        self.__check_admin()
        coworking: Optional[Coworking] = await self.coworking_repository.get(coworking_id)
        if not coworking:
            raise CoworkingDoesNotExistException()
        event: CoworkingEvent = await self.coworking_event_repository.create(coworking, event)
        return CoworkingEventResponseSchema.model_validate(event, from_attributes=True)

    async def register_coworking_seats(
            self,
            coworking_id: str,
            table_places: int,
            meeting_rooms: List[CreateSeatDTO]
    ) -> List[CoworkingSeatResponse]:
        self.__check_admin()
        coworking: Optional[Coworking] = await self.coworking_repository.get(coworking_id)
        if not coworking:
            raise CoworkingDoesNotExistException()
        seats: List[CoworkingSeat] = await self.coworking_repository.create_places(
            coworking, table_places, meeting_rooms
        )
        return [
            CoworkingSeatResponse.model_validate(seat, from_attributes=True)
            for seat in seats
        ]

    async def register_coworking_working_schedule(
            self,
            coworking_id: str,
            schedules: List[ScheduleCreateDTO]
    ) -> List[ScheduleResponseDTO]:
        self.__check_admin()
        coworking: Optional[Coworking] = await self.coworking_repository.get(coworking_id)
        if not coworking:
            raise CoworkingDoesNotExistException()
        result = await self.coworking_repository.register_schedule(coworking, schedules)
        return [
            ScheduleResponseDTO.model_validate(schedule, from_attributes=True)
            for schedule in result
        ]

    @staticmethod
    def __check_admin() -> User:
        user: Optional[User] = CONTEXT_USER.get()
        if not user:
            raise UnauthorizedError()
        if not user.is_admin:
            raise NotAdminException()
        return user
