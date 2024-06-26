import datetime
import logging
from typing import List, Optional

import fastapi_jsonrpc as jsonrpc

from common.dto.coworking import CoworkingResponseDTO, CoworkingDetailDTO
from common.dto.input_params import TimestampInterval, SearchParams
from common.dto.schedule import ScheduleResponseDTO
from common.exceptions.rpc import CoworkingDoesNotExistException
from infrastructure.database import Coworking, WorkingSchedule
from storage.coworking import AbstractCoworkingRepository
from .abstract_rpc_router import AbstractRPCRouter

logger = logging.getLogger(__name__)


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
        """
        Detail coworking response by id
        :param coworking_id: Coworking ID
        :return: CoworkingDetailDTO
        """
        logger.info("Requested coworking with id=%s", coworking_id)
        coworking: Optional[Coworking] = await self.coworking_repository.get_coworking_by_id(
            coworking_id)
        if not coworking:
            logger.error("Coworking with id=%s not found", coworking_id)
            raise CoworkingDoesNotExistException()
        logger.info("Response Coworking(id=%s, title=%s)", coworking.id, coworking.title)
        return CoworkingDetailDTO.model_validate(coworking, from_attributes=True)

    async def get_coworking_by_search_params(
            self, search: SearchParams
    ) -> List[CoworkingResponseDTO]:
        """
        Search coworking list by title and institute
        :param search: SearchParams
        :return: List[CoworkingResponseDTO]
        """
        logger.info(
            "Searching coworkings by params title = %s, institute = %s",
            search.title,
            search.institute
        )
        coworkings: List[Coworking] = await self.coworking_repository.find_by_search_params(search)
        result = []
        for coworking in coworkings:
            logger.info("Founded Coworking(id=%s, title=%s)", coworking.id, coworking.title)
            working_schedule: Optional[WorkingSchedule] = (
                await self.coworking_repository.get_coworking_schedule_at_day(datetime.date.today())
            )
            result.append(
                CoworkingResponseDTO(
                    id=coworking.id,
                    avatar=coworking.avatar,
                    title=coworking.title,
                    institute=coworking.institute,
                    description=coworking.description,
                    address=coworking.address,
                    working_schedule=ScheduleResponseDTO.model_validate(
                        working_schedule, from_attributes=True
                    ) if working_schedule else None,
                )
            )
        logger.info("Founded %s coworkings", len(result))
        return result

    async def available_coworking_by_timestamp(
            self, interval: TimestampInterval
    ) -> List[CoworkingResponseDTO]:
        """
        Search available coworking by timestamp interval
        :param interval: TimestampInterval
        :return: List[CoworkingResponseDTO]
        """
        logger.info(
            "Request coworking with interval(start=%s, end=%s)",
            interval.start,
            interval.end
        )
        available_coworking_list: List[Coworking] = (
            await self.coworking_repository.select_filter_by_timestamp_range(interval)
        )
        result = []
        for coworking in available_coworking_list:
            logger.info("Founded Coworking(id=%s, title=%s)", coworking.id, coworking.title)
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
