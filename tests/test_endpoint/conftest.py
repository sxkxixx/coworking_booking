from typing import Optional, Any, Callable

import fastapi_jsonrpc as jsonrpc
import httpx
import pytest
import pytest_asyncio
from aioredis import Redis
from starlette.middleware.base import BaseHTTPMiddleware

from common.hasher import Hasher
from common.session import TokenService
from controllers.middlewares import AuthMiddleware
from controllers.rpc import AuthRouter, ReservationRouter
from infrastructure.config import RedisSettings, ApplicationSettings
from storage.reservation.reservation_repository import ReservationRepository
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
    user_repository = UserRepository(db_manager, hasher)
    reservation_repository = ReservationRepository(db_manager)
    session_repository = RedisSessionRepository(redis, application_settings.session_ttl)
    token_service = TokenService(
        application_settings.SECRET_KEY, application_settings.access_token_ttl
    )
    # Initialize routers
    auth_router = AuthRouter(user_repository, hasher, token_service, session_repository)
    reservation_router = ReservationRouter(reservation_repository)

    # Create app and register routers
    _app = jsonrpc.API()
    _app.bind_entrypoint(auth_router.build_entrypoint())
    _app.bind_entrypoint(reservation_router.build_entrypoint())

    auth_middleware = AuthMiddleware(token_service, user_repository)
    _app.add_middleware(BaseHTTPMiddleware, dispatch=auth_middleware)

    return httpx.AsyncClient(app=_app, base_url='http://testserver')


@pytest.fixture(scope='session')
def rpc_request(async_client: httpx.AsyncClient) -> Callable:
    async def inner(
            *,
            url: str,
            method: str,
            params: Optional[Any],
            headers: Optional[dict[str, str]] = None,
            cookies: Optional[dict[str, str]] = None
    ) -> httpx.Response:
        request_body = {
            "jsonrpc": "2.0",
            "id": "0",
            "method": method,
            "params": params or {}
        }
        return await async_client.post(
            url,
            json=request_body,
            headers=headers,
            cookies=cookies
        )

    return inner


@pytest_asyncio.fixture(name='registered_user')
async def create_user(rpc_request: Callable) -> dict:
    user = {'data': {
        'email': 'name.surname@urfu.ru', 'password': 'Password1!',
        'last_name': 'Surname', 'first_name': 'Name',
        'patronymic': None,
    }}
    response: httpx.Response = await rpc_request(url='/api/v1/auth', method='register', params=user)
    return response.json()['result']


@pytest_asyncio.fixture(name="access_token")
async def authorize_user(rpc_request, registered_user) -> str:
    login_params = {'data': {
        'email': 'name.surname@urfu.ru',
        'password': 'Password1!',
        'fingerprint': 'fingerprint',
    }}
    response: httpx.Response = await rpc_request(
        url='/api/v1/auth',
        method='login',
        params=login_params
    )
    json_ = response.json()
    return json_['result']['access_token']
