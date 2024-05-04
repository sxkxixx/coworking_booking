import datetime
from typing import Optional

from pydantic import BaseModel


class DayOffSchema(BaseModel):
    coworking_id: str
    day: datetime.date
    reason: Optional[str] = None
