import datetime

from pydantic import BaseModel


class ScheduleResponseDTO(BaseModel):
    coworking_id: str
    week_day: str
    start_time: datetime.time
    end_time: datetime.time
