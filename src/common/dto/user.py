from typing import Optional

from pydantic import BaseModel, EmailStr, field_validator

from infrastructure.config import EMAIL_DOMAINS


class UserCreateDTO(BaseModel):
    email: EmailStr
    password: str
    last_name: str
    first_name: str
    patronymic: Optional[str] = None

    @field_validator('password')
    @classmethod
    def validate_password(cls, pwd: str) -> str:
        if len(pwd) < 8:
            raise ValueError('Password length gte 8 chars')
        return pwd

    @field_validator('email')
    @classmethod
    def validate_email_domain(cls, email: str) -> str:
        for domain in EMAIL_DOMAINS:
            if email.endswith(domain):
                return email
        raise ValueError('Incorrect email domain')


class UserResponseDTO(BaseModel):
    id: str
    email: EmailStr
    last_name: str
    first_name: str
    patronymic: Optional[str] = None
    is_student: bool
    avatar_filename: Optional[str] = None


class Login(BaseModel):
    email: EmailStr
    password: str
    fingerprint: str

    @field_validator('email')
    @classmethod
    def validate_email(cls, email: str) -> str:
        for domain in EMAIL_DOMAINS:
            if email.endswith(domain):
                return email
        raise ValueError('Incorrect email domain')


class TokenResponse(BaseModel):
    access_token: str
    token_header: str = 'Authorization'


class UpdateUserRequest(BaseModel):
    email: Optional[EmailStr] = None
    last_name: Optional[str] = None
    first_name: Optional[str] = None
    patronymic: Optional[str] = None

    @field_validator('email')
    @classmethod
    def validate_email_domain(cls, email: Optional[str] = None) -> str:
        if not email:
            return email
        for domain in EMAIL_DOMAINS:
            if email.endswith(domain):
                return email
        raise ValueError('Incorrect email domain')


class UserUpdateRequest(UpdateUserRequest):
    token: TokenResponse
    id: str
