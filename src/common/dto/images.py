from pydantic import BaseModel


class CoworkingImageResponse(BaseModel):
    id: int
    image_filename: str
