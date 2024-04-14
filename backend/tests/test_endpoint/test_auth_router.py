from typing import Callable

import httpx
import pytest

password: str = 'top_secret_test_pwd'
url = '/api/v1/auth'


class TestRegisterMethod:
    @pytest.mark.asyncio
    async def test_unique_user_register(self, rpc_request: Callable) -> None:
        user = {'data': {
            'email': 'name.surname@urfu.me', 'password': password,
            'last_name': 'Surname', 'first_name': 'Name',
            'patronymic': None, 'is_student': True
        }}
        response: httpx.Response = await rpc_request(url=url, method='register', params=user)
        json = response.json()
        assert json['result']['id'] == 'name.surname', json

    @pytest.mark.asyncio
    async def test_not_urfu_domain(self, rpc_request: Callable) -> None:
        user = {'data': {
            'email': 'name.surname@gmail.com', 'password': password,
            'last_name': 'Surname', 'first_name': 'Name',
            'patronymic': None, 'is_student': True
        }}
        response: httpx.Response = await rpc_request(url=url, method='register', params=user)
        json = response.json()['error']
        assert json['code'] == -32602

    @pytest.mark.asyncio
    async def test_short_password(self, rpc_request: Callable) -> None:
        user = {'data': {
            'email': 'name.surname@urfu.ru', 'password': 's',
            'last_name': 'Surname', 'first_name': 'Name',
            'patronymic': None, 'is_student': True
        }}
        response: httpx.Response = await rpc_request(url=url, method='register', params=user)
        json = response.json()['error']
        assert json['code'] == -32602

    @pytest.mark.asyncio
    async def test_not_unique_email(self, rpc_request: Callable) -> None:
        user = {'data': {
            'email': 'name.surname@urfu.ru', 'password': password,
            'last_name': 'Surname', 'first_name': 'Name',
            'patronymic': None, 'is_student': True
        }}
        await rpc_request(url=url, method='register', params=user)
        response: httpx.Response = await rpc_request(url=url, method='register', params=user)
        json = response.json()['error']
        assert json['code'] == -32001
