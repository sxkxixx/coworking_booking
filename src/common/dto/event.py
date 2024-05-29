import datetime
from typing import Optional

from pydantic import BaseModel


class CoworkingResponseSchema(BaseModel):
    coworking_id: str
    day: datetime.date
    name: str
    description: Optional[str] = None
