import datetime

from pydantic import BaseModel


class ScheduleResponseDTO(BaseModel):
    coworking_id: int
    week_day: str
    start_time: datetime.time
    end_time: datetime.time
    is_weekend: bool
