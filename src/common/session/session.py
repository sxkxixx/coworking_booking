from pydantic import BaseModel, EmailStr


class Session(BaseModel):
    user_id: str
    email: EmailStr
    fingerprint: str
