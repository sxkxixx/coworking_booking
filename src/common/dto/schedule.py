import datetime

from pydantic import BaseModel
from infrastructure.database.enum import Weekday


class ScheduleCreateDTO(BaseModel):
    week_day: Weekday
    start_time: datetime.time
    end_time: datetime.time


class ScheduleResponseDTO(ScheduleCreateDTO):
    coworking_id: str
