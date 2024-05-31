from typing import Optional

from pydantic import BaseModel


class SeatResponseDTO(BaseModel):
    id: int
    coworking_id: str
    label: Optional[str] = None
    description: Optional[str] = None
    place_type: str
    seats_count: int
