import datetime
from typing import Optional

from pydantic import BaseModel


class CoworkingEventResponseSchema(BaseModel):
    coworking_id: str
    date: datetime.date
    name: str
    description: Optional[str] = None
