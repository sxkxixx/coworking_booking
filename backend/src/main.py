from contextlib import asynccontextmanager

import fastapi_jsonrpc as jsonrpc
from aioredis import Redis

from common.hasher import Hasher
from common.session import TokenService
from controllers.rpc.auth_router import AuthRouter
from infrastructure.config import ApplicationSettings, RedisSettings
from infrastructure.database.db import manager, database
from infrastructure.database.models import *
from storage.session import RedisSessionRepository
from storage.user import UserRepository


@asynccontextmanager
async def lifespan(api: jsonrpc.API):
    models = [User, UserTelegramInfo]
    with database:
        database.create_tables(models)
    yield
    with database:
        database.drop_tables(models)


def _create_app() -> jsonrpc.API:
    # Initialize settings
    application_settings = ApplicationSettings()
    redis_settings = RedisSettings()

    redis = Redis(host=redis_settings.REDIS_HOST, port=redis_settings.REDIS_PORT)

    # Initialize utils, repositories and etc.
    hasher = Hasher()
    user_repository = UserRepository(manager)
    session_repository = RedisSessionRepository(redis, application_settings.session_ttl)
    token_service = TokenService(
        application_settings.SECRET_KEY, application_settings.access_token_ttl
    )
    # Initialize routers
    auth_router = AuthRouter(user_repository, hasher, token_service, session_repository)

    # Create app and register routers
    _app = jsonrpc.API(lifespan=lifespan)
    _app.bind_entrypoint(auth_router.build_entrypoint())

    return _app


app = _create_app()
