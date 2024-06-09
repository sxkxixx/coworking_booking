import re
from typing import Optional

from pydantic import BaseModel, EmailStr, field_validator, computed_field, Field, model_validator

from infrastructure.config import EMAIL_DOMAINS

_password_pattern = re.compile(
    r"^(?=.*[0-9].*)"  # Check a number
    r"(?=.*[a-z].*)"  # Check a-z
    r"(?=.*[A-Z].*)"  # Check A-Z 
    r"(?=.*[!,#$%&()*+-./:;<=>?@^_].*)"  # Check special char
    r"[0-9a-zA-Z!,#$%&()*+-./:;<=>?@^_]{8,}$"
)


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
        if _password_pattern.match(pwd) is None:
            raise ValueError("Password does not match the pattern")
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
    is_admin: bool = Field(default=False)
    telegram_chat_id: Optional[int] = Field(..., exclude=True)

    @computed_field
    @property
    def is_telegram_logged_in(self) -> bool:
        return self.telegram_chat_id is not None


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
    last_name: Optional[str] = None
    first_name: Optional[str] = None
    patronymic: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    password: str
    password_repeat: str
    fingerprint: str

    @field_validator('password')
    @classmethod
    def validate_pattern(cls, password: str) -> str:
        if _password_pattern.match(password) is None:
            raise ValueError('Password does not match the pattern')
        return password

    @model_validator(mode='after')
    def check_equals(self):
        if self.password != self.password_repeat:
            raise ValueError("Passwords must be equals")
        return self


class ChangePasswordResponse(BaseModel):
    access_token: str = None
    login_required: bool = True


class ResetPasswordRequest(ChangePasswordRequest):
    email: str
    token: str
