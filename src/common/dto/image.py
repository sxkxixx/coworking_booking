from pydantic import BaseModel


class ImageUrl(BaseModel):
    pre_singed_url: str
