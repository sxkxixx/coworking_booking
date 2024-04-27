from typing import List

from pydantic import BaseModel

from .day_off import DayOffSchema
from .images import CoworkingImageResponse
from .schedule import ScheduleResponseDTO
from .seats import SeatResponseDTO


class CalendarCoworking(BaseModel):
    id: str
    avatar_filename: str
    title: str


class CoworkingResponseDTO(BaseModel):
    id: str
    avatar: str
    title: str
    institute: str
    description: str
    address: str


class CoworkingDetailDTO(BaseModel):
    id: str
    avatar: str
    title: str
    institute: str
    description: str
    address: str
    seats: List[SeatResponseDTO]
    working_schedules: List[ScheduleResponseDTO]
    images: List[CoworkingImageResponse]
    days_off: List[DayOffSchema]
