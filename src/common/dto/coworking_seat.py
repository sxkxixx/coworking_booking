from pydantic import BaseModel

from infrastructure.database import PlaceType
from .coworking import CoworkingResponseDTO


class CoworkingSeatResponse(BaseModel):
    id: int
    coworking: CoworkingResponseDTO
    label: str
    description: str
    place_type: PlaceType
    seats_count: int
