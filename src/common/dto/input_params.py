from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TimestampRange(BaseModel):
    from_: datetime = Field(..., validation_alias="from")
    to_: datetime = Field(..., validation_alias="to")


class SearchParams(BaseModel):
    title: Optional[str] = None
    institute: Optional[str] = None
