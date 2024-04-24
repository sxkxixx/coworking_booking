from pydantic import BaseModel


class SeatResponseDTO(BaseModel):
    id: int
    coworking_id: str
    label: str
    description: str
    place_type: str
    seats_count: int
