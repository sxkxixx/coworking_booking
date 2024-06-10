from datetime import datetime

from pydantic import BaseModel, field_validator, model_validator, AwareDatetime

from infrastructure.database.enum import BookingStatus, PlaceType
from .coworking import CoworkingResponseDTO
from .seats import SeatResponseDTO
from ..utils import get_yekaterinburg_dt


class ReservationResponse(BaseModel):
    id: int
    session_start: AwareDatetime
    session_end: AwareDatetime
    status: BookingStatus
    created_at: datetime
    seat: SeatResponseDTO


class DetailReservationDTO(ReservationResponse):
    coworking: CoworkingResponseDTO


class ReservationCreateRequest(BaseModel):
    coworking_id: str
    place_type: PlaceType
    session_start: AwareDatetime
    session_end: AwareDatetime

    @field_validator('session_start')
    @classmethod
    def validate_date(cls, session_start: AwareDatetime) -> datetime:
        if session_start <= get_yekaterinburg_dt():
            raise ValueError(f'"session_start" must be more than %s' % get_yekaterinburg_dt())
        return session_start

    @model_validator(mode='after')
    def validate_range(self):
        if self.session_start >= self.session_end:
            raise ValueError('"session_end" can\'t be less than "session_start"')
        return self
