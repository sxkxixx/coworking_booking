from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TimestampRange(BaseModel):
    start: datetime = Field(..., validation_alias="from")
    end: datetime = Field(..., validation_alias="to")


class SearchParams(BaseModel):
    title: Optional[str] = None
    institute: Optional[str] = None
