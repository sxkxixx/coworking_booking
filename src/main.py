from contextlib import asynccontextmanager

import fastapi_jsonrpc as jsonrpc
from aioredis import Redis
from starlette.middleware.base import BaseHTTPMiddleware

from common.hasher import Hasher
from common.session import TokenService
from controllers.middlewares import AuthMiddleware
from controllers.rest import ImageRouter
from controllers.rpc.auth_router import AuthRouter
from controllers.rpc.coworking_router import CoworkingRouter
from infrastructure.config import ApplicationSettings, RedisSettings, ObjectStorageSettings
from infrastructure.database.db import manager, database
from infrastructure.database.models import *
from storage.coworking import CoworkingRepository
from storage.s3_repository import S3Repository
from storage.session import RedisSessionRepository
from storage.user import UserRepository


@asynccontextmanager
async def lifespan(api: jsonrpc.API):
    models = [
        User,
        Coworking,
        Reservation,
        CoworkingSeat,
        NonBusinessDay,
        CoworkingImages,
        WorkingSchedule,
        UserTelegramInfo
    ]
    with database:
        database.create_tables(models)
    yield
    # with database:
    #     database.drop_tables(models)


def _create_app() -> jsonrpc.API:
    # Initialize settings
    application_settings = ApplicationSettings()
    redis_settings = RedisSettings()
    object_storage_settings = ObjectStorageSettings()

    redis = Redis(host=redis_settings.REDIS_HOST, port=redis_settings.REDIS_PORT)

    # Initialize utils, repositories and etc.
    hasher = Hasher()
    user_repository = UserRepository(manager)
    coworking_repository = CoworkingRepository(manager)
    session_repository = RedisSessionRepository(redis, application_settings.session_ttl)
    token_service = TokenService(
        application_settings.SECRET_KEY, application_settings.access_token_ttl
    )
    s3_repository = S3Repository(object_storage_settings)
    # Initialize routers
    auth_router = AuthRouter(user_repository, hasher, token_service, session_repository)
    image_router = ImageRouter(user_repository, s3_repository)
    coworking_router = CoworkingRouter(coworking_repository)

    # Middlewares
    auth_middleware = AuthMiddleware(token_service, user_repository)

    # Create app and register routers
    _app = jsonrpc.API(lifespan=lifespan)
    _app.bind_entrypoint(auth_router.build_entrypoint())
    _app.bind_entrypoint(coworking_router.build_entrypoint())
    _app.include_router(image_router.build_api_router())

    _app.add_middleware(BaseHTTPMiddleware, dispatch=auth_middleware)

    return _app


app = _create_app()
