from typing import Optional, Any, Callable

import fastapi_jsonrpc as jsonrpc
import httpx
import pytest
import pytest_asyncio
from aioredis import Redis

from common.hasher import Hasher
from common.session import TokenService
from controllers.rpc import AuthRouter
from infrastructure.config import RedisSettings, ApplicationSettings
from storage.session import RedisSessionRepository
from storage.user import UserRepository


@pytest.fixture(scope='session')
def async_client(db_manager) -> httpx.AsyncClient:
    # Initialize settings
    application_settings = ApplicationSettings()
    redis_settings = RedisSettings()

    redis = Redis(host=redis_settings.REDIS_HOST, port=redis_settings.REDIS_PORT)

    # Initialize utils, repositories and etc.
    hasher = Hasher()
    user_repository = UserRepository(db_manager)
    session_repository = RedisSessionRepository(redis, application_settings.session_ttl)
    token_service = TokenService(
        application_settings.SECRET_KEY, application_settings.access_token_ttl
    )
    # Initialize routers
    auth_router = AuthRouter(user_repository, hasher, token_service, session_repository)

    # Create app and register routers
    _app = jsonrpc.API()
    _app.bind_entrypoint(auth_router.build_entrypoint())
    return httpx.AsyncClient(app=_app, base_url='http://testserver')


@pytest.fixture(scope='session')
def rpc_request(async_client: httpx.AsyncClient) -> Callable:
    async def inner(
            *,
            url: str,
            method: str,
            params: Optional[Any],
            headers: Optional[dict] = None
    ) -> httpx.Response:
        request_body = {
            "jsonrpc": "2.0",
            "id": "0",
            "method": method,
            "params": params or {}
        }
        return await async_client.post(url, json=request_body, headers=headers or {})

    return inner


@pytest_asyncio.fixture(name='registered_user')
async def create_user(rpc_request: Callable) -> dict:
    user = {'data': {
        'email': 'name.surname@urfu.ru', 'password': 'top_secret_test_pwd',
        'last_name': 'Surname', 'first_name': 'Name',
        'patronymic': None, 'is_student': True
    }}
    response: httpx.Response = await rpc_request(url='/api/v1/auth', method='register', params=user)
    return response.json()['result']
