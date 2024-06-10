from datetime import datetime
from typing import Optional, Union

from pydantic import BaseModel, Field, model_validator, AwareDatetime


class TimestampRange(BaseModel):
    start: Union[datetime, AwareDatetime] = Field(..., validation_alias="from")
    end: Union[datetime, AwareDatetime] = Field(..., validation_alias="to")

    @model_validator(mode="after")
    def validate_range(self):
        if self.end <= self.start:
            raise ValueError("Range end can\'t be less that range start")
        return self

    @model_validator(mode="after")
    def validate_range_dates(self):
        if self.end.date() != self.start.date():
            raise ValueError("Dates of 'from' and 'to' must be equals")
        return self


class SearchParams(BaseModel):
    title: Optional[str] = None
    institute: Optional[str] = None
