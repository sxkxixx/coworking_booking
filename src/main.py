from contextlib import asynccontextmanager

import fastapi_jsonrpc as jsonrpc
import jinja2
from aioredis import Redis
from fastapi.middleware.cors import CORSMiddleware
from jinja2 import FileSystemLoader
from starlette.middleware.base import BaseHTTPMiddleware

from common.hasher import Hasher
from common.service.reset_password_send_service import PasswordResetSendService
from common.session import TokenService
from controllers.middlewares import AuthMiddleware
from controllers.rest import ImageRouter
from controllers.rpc import (
    AuthRouter,
    ReservationRouter,
    CoworkingRouter,
    UserRouter,
    UserSettingsRouter, AdminCoworkingRouter
)
from infrastructure.config import (
    ApplicationSettings,
    RedisSettings,
    ObjectStorageSettings,
    InfrastructureSettings,
    SMTPSettings
)
from infrastructure.database.db import manager, database
from infrastructure.database.models import *
from infrastructure.logging import configure_logging
from storage.coworking import CoworkingRepository
from storage.coworking_event import CoworkingEventRepository
from storage.password_reset_token import PasswordResetTokenRepository
from storage.reservation.reservation_repository import ReservationRepository
from storage.s3_repository import S3Repository
from storage.session import RedisSessionRepository
from storage.user import UserRepository


@asynccontextmanager
async def lifespan(_api: jsonrpc.API):
    models = [
        User,
        Coworking,
        Reservation,
        CoworkingSeat,
        CoworkingEvent,
        CoworkingImages,
        WorkingSchedule,
        EmailAuthData,
        PasswordResetToken,
        TechCapability
    ]
    with database:
        database.create_tables(models)
    yield


def _create_app() -> jsonrpc.API:
    # Initialize settings
    configure_logging()

    application_settings = ApplicationSettings()
    redis_settings = RedisSettings()
    object_storage_settings = ObjectStorageSettings()
    smtp_settings = SMTPSettings()
    infra_settings = InfrastructureSettings()

    jinja2_env = jinja2.Environment(
        loader=FileSystemLoader('/templates'),
        enable_async=True
    )

    redis = Redis(host=redis_settings.REDIS_HOST, port=redis_settings.REDIS_PORT)

    # Initialize utils, repositories and etc.
    hasher = Hasher()
    user_repository = UserRepository(manager, hasher)
    coworking_repository = CoworkingRepository(manager)
    session_repository = RedisSessionRepository(redis, application_settings.session_ttl)
    coworking_event_repository = CoworkingEventRepository(manager)
    token_service = TokenService(
        application_settings.SECRET_KEY, application_settings.access_token_ttl
    )
    s3_repository = S3Repository(object_storage_settings)
    reservation_repository = ReservationRepository(manager)
    password_reset_token_repo = PasswordResetTokenRepository(manager)

    # Services
    send_reset_password_message_service = PasswordResetSendService(
        jinja2_env, smtp_settings, infra_settings
    )

    # Initialize routers
    auth_router = AuthRouter(user_repository, hasher, token_service, session_repository)
    image_router = ImageRouter(user_repository, s3_repository)
    user_router = UserRouter(user_repository, token_service)
    reservation_router = ReservationRouter(reservation_repository)
    coworking_router = CoworkingRouter(coworking_repository)
    user_settings_router = UserSettingsRouter(
        user_repository,
        password_reset_token_repo,
        send_reset_password_message_service,
        hasher
    )
    admin_coworking_router = AdminCoworkingRouter(
        coworking_repository, coworking_event_repository, s3_repository
    )

    # Middlewares

    # Create app and register routers
    _app = jsonrpc.API(lifespan=lifespan)
    _app.bind_entrypoint(auth_router.build_entrypoint())
    _app.bind_entrypoint(coworking_router.build_entrypoint())
    _app.include_router(image_router.build_api_router())
    _app.bind_entrypoint(user_router.build_entrypoint())
    _app.bind_entrypoint(reservation_router.build_entrypoint())
    _app.bind_entrypoint(user_settings_router.build_entrypoint())
    _app.bind_entrypoint(admin_coworking_router.build_entrypoint())

    auth_middleware = AuthMiddleware(token_service, user_repository)
    _app.add_middleware(BaseHTTPMiddleware, dispatch=auth_middleware)

    _app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    return _app


app = _create_app()
