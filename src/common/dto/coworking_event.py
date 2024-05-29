from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class CoworkingEventSchema(BaseModel):
    event_date: date = Field(..., validation_alias="date", serialization_alias="date")
    name: str
    description: Optional[str]


class CoworkingEventResponseSchema(CoworkingEventSchema):
    id: int
    coworking_id: str
