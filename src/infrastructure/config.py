from datetime import timedelta

import dotenv
from pydantic import computed_field
from pydantic_settings import BaseSettings

dotenv.load_dotenv('.env')

EMAIL_DOMAINS = ['urfu.me', 'urfu.ru']


class DatabaseSettings(BaseSettings):
    DATABASE_USER: str
    DATABASE_PASSWORD: str
    DATABASE_HOST: str
    DATABASE_PORT: str
    DATABASE_NAME: str


class RedisSettings(BaseSettings):
    REDIS_HOST: str
    REDIS_PORT: int


class ApplicationSettings(BaseSettings):
    SECRET_KEY: str
    ACCESS_TOKEN_TTL_MINUTES: int
    SESSION_TTL_DAYS: int

    @computed_field
    @property
    def access_token_ttl(self) -> timedelta:
        return timedelta(minutes=self.ACCESS_TOKEN_TTL_MINUTES)

    @computed_field
    @property
    def session_ttl(self) -> timedelta:
        return timedelta(days=self.SESSION_TTL_DAYS)


class ObjectStorageSettings(BaseSettings):
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    REGION_NAME: str
    BUCKET_NAME: str
    S3_ENDPOINT_URL: str


class SMTPSettings(BaseSettings):
    SMTP_EMAIL: str
    SMTP_PASSWORD: str
    SMTP_SERVER: str
    SMTP_PORT: int


class InfrastructureSettings(BaseSettings):
    FRONTEND_URL: str = 'http://localhost:3000'
