from typing import Optional

from pydantic import BaseModel, Field

from infrastructure.database import PlaceType


class CreateSeatDTO(BaseModel):
    label: str
    description: Optional[str]
    seats_count: int


class CoworkingSeatResponse(BaseModel):
    id: int
    coworking_id: str
    label: Optional[str] = None
    description: Optional[str]
    place_type: PlaceType
    seats_count: int
