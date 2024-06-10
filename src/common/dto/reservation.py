from datetime import datetime

from pydantic import BaseModel, field_validator, model_validator, NaiveDatetime

from infrastructure.database.enum import BookingStatus, PlaceType
from .coworking import CoworkingResponseDTO
from .seats import SeatResponseDTO


class ReservationResponse(BaseModel):
    id: int
    session_start: NaiveDatetime
    session_end: NaiveDatetime
    status: BookingStatus
    created_at: datetime
    seat: SeatResponseDTO


class DetailReservationDTO(ReservationResponse):
    coworking: CoworkingResponseDTO


class ReservationCreateRequest(BaseModel):
    coworking_id: str
    place_type: PlaceType
    session_start: NaiveDatetime
    session_end: NaiveDatetime

    @classmethod
    @field_validator('session_start')
    def validate_date(cls, session_start: datetime) -> datetime:
        if session_start <= datetime.utcnow():
            raise ValueError('"session_start" must be more than current time')
        return session_start

    @model_validator(mode='after')
    def validate_range(self):
        if self.session_start >= self.session_end:
            raise ValueError('"session_end" can\'t be less than "session_start"')
        return self
