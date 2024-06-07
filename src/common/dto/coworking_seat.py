from typing import Optional

from pydantic import BaseModel

from infrastructure.database import PlaceType


class CreateSeatDTO(BaseModel):
    label: str
    description: Optional[str] = None
    seats_count: int


class CoworkingSeatResponse(BaseModel):
    id: int
    coworking_id: str
    label: Optional[str] = None
    description: Optional[str] = None
    place_type: PlaceType
    seats_count: int
