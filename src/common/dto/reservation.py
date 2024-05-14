from datetime import datetime

from pydantic import BaseModel, field_validator, model_validator

from common.dto.seats import SeatResponseDTO
from infrastructure.database.enum import BookingStatus, PlaceType


class ReservationResponse(BaseModel):
    id: int
    seat: SeatResponseDTO
    session_start: datetime
    session_end: datetime
    status: BookingStatus
    created_at: datetime


class ReservationCreateRequest(BaseModel):
    coworking_id: str
    place_type: PlaceType
    session_start: datetime
    session_end: datetime

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
