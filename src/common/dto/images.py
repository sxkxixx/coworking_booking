from pydantic import BaseModel


class CoworkingImageResponse(BaseModel):
    image_filename: str
