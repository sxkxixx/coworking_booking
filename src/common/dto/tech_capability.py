from pydantic import BaseModel


class TechCapabilitySchema(BaseModel):
    capability: str
