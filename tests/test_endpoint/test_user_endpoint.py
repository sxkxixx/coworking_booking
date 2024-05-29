from typing import Callable

import httpx
import pytest
from peewee_async import Manager

from infrastructure.database import User


class TestUpdateUserInfo:
    @pytest.mark.asyncio
    async def test_update_all_params(self, rpc_request: Callable, db_manager: Manager) -> None:
        await rpc_request(
            url="/api/v1/auth",
            method="register",
            params={"data": {
                "email": "name.surname@urfu.me",
                "password": "Password1!",
                "last_name": "Surname",
                "first_name": "Name",
                "patronymic": None
            }}
        )
        login_response: httpx.Response = await rpc_request(
            url="/api/v1/auth",
            method="login",
            params={"data": {
                "email": "name.surname@urfu.me",
                "password": "Password1!",
                "fingerprint": "fingerprint",
            }}
        )
        login_json = login_response.json()
        assert login_json.get("error") is None
        access_token: str = login_json["result"]["access_token"]
        await rpc_request(
            url="/api/v1/user",
            method="update_user_data",
            params={"values_set": {
                "last_name": "NewSurname",
                "first_name": "NoName",
                "patronymic": "Patronymic",
            }},
            headers={"Authorization": access_token}
        )
        user: User = await db_manager.get(User, User.email == "name.surname@urfu.me")
        assert user.last_name == "NewSurname"
        assert user.first_name == "NoName"
        assert user.patronymic == "Patronymic"

    @pytest.mark.asyncio
    async def test_update_without_access_token(
            self,
            rpc_request: Callable,
            db_manager: Manager
    ) -> None:
        response: httpx.Response = await rpc_request(
            url="/api/v1/user",
            method="update_user_data",
            params={"values_set": {
                "last_name": "NewSurname",
                "first_name": "NoName",
                "patronymic": "Patronymic",
            }}
        )
        json = response.json()
        assert json["error"]["code"] == -32004

    @pytest.mark.asyncio
    async def test_update_no_values_set(self, rpc_request: Callable, db_manager: Manager) -> None:
        await rpc_request(
            url="/api/v1/auth",
            method="register",
            params={"data": {
                "email": "name.surname@urfu.me",
                "password": "Password1!",
                "last_name": "Surname",
                "first_name": "Name",
                "patronymic": None
            }}
        )
        login_response: httpx.Response = await rpc_request(
            url="/api/v1/auth",
            method="login",
            params={"data": {
                "email": "name.surname@urfu.me",
                "password": "Password1!",
                "fingerprint": "fingerprint",
            }}
        )
        login_json = login_response.json()
        assert login_json.get("error") is None
        access_token: str = login_json["result"]["access_token"]
        await rpc_request(
            url="/api/v1/user",
            method="update_user_data",
            params={"values_set": {}},
            headers={"Authorization": access_token}
        )
        user: User = await db_manager.get(User, User.email == "name.surname@urfu.me")
        assert user.last_name == "Surname"
        assert user.first_name == "Name"
        assert user.patronymic is None
