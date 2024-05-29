import datetime
import os
from typing import Callable

import httpx
import pytest
import pytest_asyncio
from peewee_async import Manager

from infrastructure.database import User, Coworking

url: str = "/api/v1/admin/coworking"


@pytest_asyncio.fixture()
async def admin_access_token(rpc_request: Callable, db_manager: Manager) -> str:
    await rpc_request(
        url="/api/v1/auth", method="register",
        params={"data": {
            "email": "admin.surname@urfu.me",
            "password": "TopSecret1!",
            "last_name": "Surname",
            "first_name": "Admin",
        }}
    )
    user = await db_manager.get(User, User.email == "admin.surname@urfu.me")
    user.is_admin = True
    await db_manager.update(user)
    response: httpx.Response = await rpc_request(
        url="/api/v1/auth", method="login",
        params={"data": {
            "email": "admin.surname@urfu.me",
            "password": "TopSecret1!",
            "fingerprint": "any",
        }}
    )
    json_ = response.json()
    return json_["result"]["access_token"]


class TestCreateCoworking:
    @pytest.mark.asyncio
    async def test_no_user(self, rpc_request: Callable) -> None:
        response: httpx.Response = await rpc_request(
            url=url,
            method="create_coworking",
            params={"coworking": {
                "title": "null", "institute": "null", "description": "null", "address": "null",
            }},
        )
        json_ = response.json()
        assert json_.get('error')
        assert json_['error']['code'] == -32004

    @pytest.mark.asyncio
    async def test_user_not_admin(self, rpc_request: Callable, access_token: str) -> None:
        response: httpx.Response = await rpc_request(
            url=url,
            method="create_coworking",
            params={"coworking": {
                "title": "null", "institute": "null", "description": "null", "address": "null",
            }},
            headers={'Authorization': access_token}
        )
        json_ = response.json()
        assert json_.get('error')
        assert json_['error']['code'] == -32009

    @pytest.mark.asyncio
    async def test_create_coworking(self, rpc_request: Callable, admin_access_token: str) -> None:
        response: httpx.Response = await rpc_request(
            url=url,
            method="create_coworking",
            params={"coworking": {
                "title": "Антресоли", "institute": "null", "description": "null", "address": "null",
            }},
            headers={'Authorization': admin_access_token}
        )
        json_ = response.json()
        assert not json_.get('error', None)
        assert json_['result']["title"] == "Антресоли"


class TestCreateCoworkingEvent:
    @pytest.mark.asyncio
    async def test_coworking_not_exists(self, rpc_request: Callable, admin_access_token: str):
        response: httpx.Response = await rpc_request(
            url=url,
            method="create_coworking_event",
            params={
                "coworking_id": os.urandom(16).hex(),
                "event": {
                    "date": datetime.date.today().isoformat(),
                    "name": "Мероприятия",
                    "description": "description",
                }
            },
            headers={"Authorization": admin_access_token}
        )
        json_ = response.json()
        assert json_.get('error')
        assert json_['error']['code'] == -32008

    @pytest.mark.asyncio
    async def test_create_coworking_event(
            self,
            rpc_request: Callable,
            db_manager: Manager,
            admin_access_token: str
    ) -> None:
        coworking: Coworking = await db_manager.create(
            Coworking,
            title="Антресоли",
            institute="ГУК",
            description="Коворкинг",
            address="Мира, д.19",
        )
        response: httpx.Response = await rpc_request(
            url=url,
            method="create_coworking_event",
            params={
                "coworking_id": coworking.id,
                "event": {
                    "date": datetime.date.today().isoformat(),
                    "name": "Мероприятия",
                    "description": "description",
                }
            },
            headers={"Authorization": admin_access_token}
        )
        json_ = response.json()
        assert not json_.get('error', None)
        assert json_['result']['coworking_id'] == coworking.id


class TestCreateCapabilities:
    @pytest.mark.asyncio
    async def test_create(
            self,
            rpc_request: Callable,
            admin_access_token: str,
            db_manager: Manager
    ) -> None:
        coworking: Coworking = await db_manager.create(
            Coworking,
            title="Антресоли",
            institute="ГУК",
            description="Коворкинг",
            address="Мира, д.19",
        )
        response: httpx.Response = await rpc_request(
            url=url,
            method="create_coworking_tech_capabilities",
            params={
                "coworking_id": coworking.id,
                "capabilities": [
                    {"capability": "Wi-Fi"},
                    {"capability": "Маркерная доска"},
                ]
            },
            headers={"Authorization": admin_access_token}
        )
        json_ = response.json()
        assert json_.get('result', None), json_
        assert len(json_['result']) == 2


class TestRegisterCoworkingSeats:
    @pytest.mark.asyncio
    async def test_create_seats(
            self,
            rpc_request: Callable,
            db_manager: Manager,
            admin_access_token: str
    ) -> None:
        coworking: Coworking = await db_manager.create(
            Coworking,
            title="Антресоли",
            institute="ГУК",
            description="Коворкинг",
            address="Мира, д.19",
        )
        response: httpx.Response = await rpc_request(
            url=url,
            method="register_coworking_seats",
            params={
                "coworking_id": coworking.id,
                "table_places": 5,
                "meeting_rooms": [
                    {
                        "label": "Метка",
                        "description": "Описание",
                        "seats_count": 14
                    }
                ],
            },
            headers={"Authorization": admin_access_token}
        )
        json_ = response.json()
        assert json_.get('result'), json_
        assert len(json_['result']) == 6
