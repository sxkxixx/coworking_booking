from typing import Callable

import httpx
import pytest

url = '/api/v1/auth'


class TestRegisterMethod:
    @pytest.mark.asyncio
    async def test_unique_user_register(self, rpc_request: Callable) -> None:
        """
        Простой тест на корректную работу метода
        """
        user = {'data': {
            'email': 'name.surname@urfu.me', 'password': 'top_secret_test_pwd',
            'last_name': 'Surname', 'first_name': 'Name',
            'patronymic': None, 'is_student': True
        }}
        response: httpx.Response = await rpc_request(url=url, method='register', params=user)
        json = response.json()
        assert json['result']['id'] == 'name.surname', json

    @pytest.mark.asyncio
    async def test_not_urfu_domain(self, rpc_request: Callable) -> None:
        """
        Проверка валидации на почтовый домен, не принадлежащий к корпоративному УрФУ
        """
        user = {'data': {
            'email': 'name.surname@gmail.com', 'password': 'top_secret_test_pwd',
            'last_name': 'Surname', 'first_name': 'Name',
            'patronymic': None, 'is_student': True
        }}
        response: httpx.Response = await rpc_request(url=url, method='register', params=user)
        json = response.json()['error']
        assert json['code'] == -32602

    @pytest.mark.asyncio
    async def test_short_password(self, rpc_request: Callable) -> None:
        """Валиация на корреткий пароль"""
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
        """Валидация на неуникальный email"""
        user = {'data': {
            'email': 'name.surname@urfu.ru', 'password': 'top_secret_test_pwd',
            'last_name': 'Surname', 'first_name': 'Name',
            'patronymic': None, 'is_student': True
        }}
        await rpc_request(url=url, method='register', params=user)
        response: httpx.Response = await rpc_request(url=url, method='register', params=user)
        json = response.json()['error']
        assert json['code'] == -32001


class TestLoginMethod:
    @pytest.mark.asyncio
    async def test_no_registered_user(self, rpc_request: Callable) -> None:
        """
        Тестирует что невозможно аутентифицировать пользователя, который не был зарегистрирован
        """
        credentials = {'data': {
            'email': 'name.surname@urfu.ru',
            'password': 'top_secret_test_pwd',
            'fingerprint': 'fingerprint'
        }}
        response: httpx.Response = await rpc_request(url=url, method='login', params=credentials)
        json_ = response.json()
        assert json_['error']['code'] == -32002

    @pytest.mark.asyncio
    async def test_fixture_is_working(self, rpc_request: Callable, registered_user: dict) -> None:
        """Проверка работоспособности фикстуры и наличия токенов"""
        credentials = {'data': {
            'email': 'name.surname@urfu.ru',
            'password': 'top_secret_test_pwd',
            'fingerprint': 'fingerprint'
        }}
        response: httpx.Response = await rpc_request(url=url, method='login', params=credentials)
        json_ = response.json()
        assert json_['result']['access_token'] is not None
        assert response.cookies.get('refresh_token', None)

    @pytest.mark.asyncio
    async def test_incorrect_password(self, rpc_request: Callable, registered_user: dict) -> None:
        """Проверка на -32002 код при неправильном пароле"""
        credentials = {'data': {
            'email': 'name.surname@urfu.ru',
            'password': 'change_me',
            'fingerprint': 'fingerprint'
        }}
        response: httpx.Response = await rpc_request(url=url, method='login', params=credentials)
        json_ = response.json()
        assert json_['error']['code'] == -32002
        assert not response.cookies.get('refresh_token', None)


class TestRefreshSession:
    @pytest.mark.asyncio
    async def test_no_refresh_token(self, rpc_request: Callable) -> None:
        params = {'fingerprint': 'string'}
        response: httpx.Response = await rpc_request(
            url=url, method='refresh_session', params=params
        )
        json_ = response.json()
        assert json_['error']['code'] == -32003

    @pytest.mark.asyncio
    async def test_no_session(self, rpc_request: Callable) -> None:
        params = {'fingerprint': 'string'}
        cookies = {'refresh_token': 'refresh_token'}
        response: httpx.Response = await rpc_request(
            url=url, method='refresh_session', params=params, cookies=cookies
        )
        with pytest.raises(KeyError):
            _ = response.cookies['refresh_session']
        json_ = response.json()
        assert json_['error']['code'] == -32003

    @pytest.mark.asyncio
    async def test_incorrect_fingerprint(
            self, rpc_request: Callable, registered_user: dict
    ) -> None:
        login_params = {'data': {
            'email': 'name.surname@urfu.ru',
            'password': 'top_secret_test_pwd',
            'fingerprint': 'any'
        }}
        login_response: httpx.Response = await rpc_request(
            url=url, method='login', params=login_params
        )
        assert login_response.json().get('error') is None
        assert (refresh_token := login_response.cookies.get('refresh_token')) is not None

        refresh_session_params = {'fingerprint': 'another'}
        refresh_response: httpx.Response = await rpc_request(
            url=url, method='refresh_session',
            params=refresh_session_params, cookies={'refresh_token': refresh_token}
        )
        json_ = refresh_response.json()
        assert json_['error']['code'] == -32003
