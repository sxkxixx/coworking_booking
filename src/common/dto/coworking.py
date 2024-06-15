from typing import List, Optional

from pydantic import BaseModel

from .event import CoworkingEventResponseSchema
from .images import CoworkingImageResponse
from .schedule import ScheduleResponseDTO
from .seats import SeatResponseDTO
from .tech_capability import TechCapabilitySchema


class CoworkingCreateDTO(BaseModel):
    title: str
    institute: str
    description: str
    address: str


class CoworkingResponseDTO(BaseModel):
    id: str
    avatar: Optional[str] = None
    title: str
    institute: str
    description: str
    address: str
    working_schedule: Optional[ScheduleResponseDTO] = None


class CoworkingDetailDTO(BaseModel):
    id: str
    avatar: Optional[str] = None
    title: str
    institute: str
    description: str
    address: str
    seats: List[SeatResponseDTO]
    working_schedules: List[ScheduleResponseDTO]
    images: List[CoworkingImageResponse]
    events: List[CoworkingEventResponseSchema]
    technical_capabilities: List[TechCapabilitySchema]
