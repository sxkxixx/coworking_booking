from typing import List, Optional

import fastapi_jsonrpc as jsonrpc

from common.dto.coworking import CoworkingResponseDTO, CoworkingDetailDTO
from common.dto.input_params import TimestampRange, SearchParams
from common.dto.schedule import ScheduleResponseDTO
from common.exceptions.rpc import CoworkingDoesNotExistException
from infrastructure.database import Coworking, WorkingSchedule
from storage.coworking import AbstractCoworkingRepository
from .abstract_rpc_router import AbstractRPCRouter


class CoworkingRouter(AbstractRPCRouter):
    def __init__(self, coworking_repository: AbstractCoworkingRepository):
        self.coworking_repository = coworking_repository

    def build_entrypoint(self) -> jsonrpc.Entrypoint:
        entrypoint = jsonrpc.Entrypoint(path='/api/v1/coworking', tags=['COWORKING'])
        entrypoint.add_method_route(self.available_coworking_by_timestamp)
        entrypoint.add_method_route(self.get_coworking_by_search_params)
        entrypoint.add_method_route(self.get_coworking, errors=[CoworkingDoesNotExistException])
        return entrypoint

    async def get_coworking(self, coworking_id: str) -> CoworkingDetailDTO:
        coworking: Optional[Coworking] = await self.coworking_repository.get_coworking_by_id(
            coworking_id)
        if not coworking:
            raise CoworkingDoesNotExistException()
        return CoworkingDetailDTO.model_validate(coworking, from_attributes=True)

    async def get_coworking_by_search_params(
            self, search: SearchParams
    ) -> List[CoworkingResponseDTO]:
        """Поля title, institute могут быть равны значению null"""
        coworking_list = await self.coworking_repository.find_by_search_params(search)
        response_data = [
            CoworkingResponseDTO.model_validate(coworking, from_attributes=True)
            for coworking in coworking_list
        ]
        return response_data

    async def available_coworking_by_timestamp(
            self, interval: TimestampRange
    ) -> List[CoworkingResponseDTO]:
        available_coworking_list: List[Coworking] = (
            await self.coworking_repository.select_filter_by_timestamp_range(interval)
        )
        result = []
        for coworking in available_coworking_list:
            working_time: Optional[WorkingSchedule] = (
                await self.coworking_repository.get_coworking_schedule_at_day(interval.start)
            )
            validated = CoworkingResponseDTO(
                id=coworking.id,
                avatar=coworking.avatar,
                title=coworking.title,
                institute=coworking.institute,
                description=coworking.description,
                address=coworking.address,
                working_schedule=ScheduleResponseDTO.model_validate(
                    working_time, from_attributes=True
                ) if working_time else None,
            )
            result.append(validated)
        return result
