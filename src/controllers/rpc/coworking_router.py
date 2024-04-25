from typing import List, Optional

import fastapi_jsonrpc as jsonrpc

from common.dto.coworking import CoworkingResponseDTO, CoworkingDetailDTO
from common.dto.input_params import TimestampRange, SearchParams
from infrastructure.database import Coworking
from storage.coworking import AbstractCoworkingRepository
from .abstract_rpc_router import AbstractRPCRouter


class CoworkingRouter(AbstractRPCRouter):
    def __init__(self, coworking_repository: AbstractCoworkingRepository):
        self.coworking_repository = coworking_repository

    def build_entrypoint(self) -> jsonrpc.Entrypoint:
        entrypoint = jsonrpc.Entrypoint(path='/api/v1/coworking', tags=['COWORKING'])
        entrypoint.add_method_route(self.available_coworking_by_timestamp)
        entrypoint.add_method_route(self.get_coworking_by_search_params)
        entrypoint.add_method_route(self.get_coworking)
        return entrypoint

    async def get_coworking(self, coworking_id: str) -> CoworkingDetailDTO:
        coworking: Optional[Coworking] = await self.coworking_repository.get_coworking_by_id(
            coworking_id)
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
        available_coworking_list = await self.coworking_repository.select_filter_by_timestamp_range(interval)
        return [
            CoworkingResponseDTO.model_validate(coworking, from_attributes=True)
            for coworking in available_coworking_list
        ]
