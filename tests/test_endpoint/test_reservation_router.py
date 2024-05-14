import datetime
import logging
from typing import Callable

import httpx
import pytest
import pytest_asyncio
from peewee_async import Manager

from infrastructure.database import PlaceType
from infrastructure.database.models import Coworking, CoworkingSeat, NonBusinessDay


@pytest_asyncio.fixture()
async def create_coworking(db_manager: Manager) -> Coworking:
    return await db_manager.create(
        Coworking,
        id="id",
        avatar="any_image.jpeg",
        title="Антресоли",
        institute="ГУК",
        description="Описание",
        address="Мира 19",
    )


@pytest_asyncio.fixture()
async def create_coworking_seat(create_coworking: Coworking, db_manager: Manager) -> CoworkingSeat:
    return await db_manager.create(
        CoworkingSeat,
        coworking=create_coworking,
        label="meeting-room-1",
        description="Описание",
        place_type=PlaceType.MEETING_ROOM,
        seats_count=20,
    )


@pytest_asyncio.fixture()
async def create_non_business_day(
        db_manager: Manager,
        create_coworking: Coworking
) -> NonBusinessDay:
    return await db_manager.create(
        NonBusinessDay,
        coworking=create_coworking,
        day=datetime.date(2024, 5, 10),
    )


class TestCreateReservationMethod:
    @pytest.mark.asyncio
    async def test_create_reservation_if_coworking_not_exists(
            self,
            rpc_request: Callable,
            access_token: str,
    ):
        reservation = {'reservation': {
            'coworking_id': "Random_ID", 'place_type': 'meeting_room',
            'session_start': "2024-05-10 11:00:00",
            'session_end': "2024-05-10 12:00:00",
        }}
        response: httpx.Response = await rpc_request(
            url='/api/v1/reservation',
            method='create_reservation',
            params=reservation,
            headers={"Authorization": access_token}
        )
        json_ = response.json()
        logging.info(json_)
        assert json_['error']['code'] == -32005

    @pytest.mark.asyncio
    async def test_create_reservation_without_conflicts(
            self,
            rpc_request: Callable,
            access_token: str,
            create_coworking: Coworking,
            create_coworking_seat: CoworkingSeat
    ) -> None:
        current_time = datetime.datetime.now()
        session_start = current_time + datetime.timedelta(hours=1)
        session_end = session_start + datetime.timedelta(hours=1)
        reservation = {'reservation': {
            'coworking_id': create_coworking.id, 'place_type': 'meeting_room',
            'session_start': session_start.isoformat(),
            'session_end': session_end.isoformat(),
        }}
        response: httpx.Response = await rpc_request(
            url='/api/v1/reservation',
            method='create_reservation',
            params=reservation,
            headers={"Authorization": access_token}
        )
        json_ = response.json()
        assert json_.get('error', None) is None
        result = json_['result']
        assert result['status'] == 'new'

    @pytest.mark.asyncio
    async def test_create_reservation_with_confirmed_status(
            self,
            rpc_request: Callable,
            access_token: str,
            create_coworking: Coworking,
            create_coworking_seat: CoworkingSeat
    ) -> None:
        current_time = datetime.datetime.utcnow()
        session_start = current_time + datetime.timedelta(minutes=15)
        session_end = session_start + datetime.timedelta(hours=1)
        reservation = {'reservation': {
            'coworking_id': create_coworking.id, 'place_type': 'meeting_room',
            'session_start': session_start.isoformat(),
            'session_end': session_end.isoformat(),
        }}
        response: httpx.Response = await rpc_request(
            url='/api/v1/reservation',
            method='create_reservation',
            params=reservation,
            headers={"Authorization": access_token}
        )
        json_ = response.json()
        assert json_.get('error', None) is None
        result = json_['result']
        assert result['status'] == 'confirmed'

    @pytest.mark.asyncio
    async def test_create_with_left_conflict(
            self,
            rpc_request: Callable,
            access_token: str,
            create_coworking: Coworking,
            create_coworking_seat: CoworkingSeat
    ) -> None:
        first_reservation = {'reservation': {
            'coworking_id': create_coworking.id, 'place_type': 'meeting_room',
            'session_start': datetime.datetime(2025, 5, 1, 13).isoformat(),
            'session_end': datetime.datetime(2025, 5, 1, 14).isoformat(),
        }}
        first_response: httpx.Response = await rpc_request(
            url='/api/v1/reservation',
            method='create_reservation',
            params=first_reservation,
            headers={"Authorization": access_token}
        )
        assert not first_response.json().get('error', None)

        second_reservation = {'reservation': {
            'coworking_id': create_coworking.id, 'place_type': 'meeting_room',
            'session_start': datetime.datetime(2025, 5, 1, 13, 30).isoformat(),
            'session_end': datetime.datetime(2025, 5, 1, 14, 30).isoformat(),
        }}

        second_response: httpx.Response = await rpc_request(
            url='/api/v1/reservation',
            method='create_reservation',
            params=second_reservation,
            headers={"Authorization": access_token}
        )
        json_ = second_response.json()
        assert json_['error']['code'] == -32005

    @pytest.mark.asyncio
    async def test_create_with_right_conflict(
            self,
            rpc_request: Callable,
            access_token: str,
            create_coworking: Coworking,
            create_coworking_seat: CoworkingSeat
    ) -> None:
        first_reservation = {'reservation': {
            'coworking_id': create_coworking.id, 'place_type': 'meeting_room',
            'session_start': datetime.datetime(2025, 5, 1, 13).isoformat(),
            'session_end': datetime.datetime(2025, 5, 1, 14).isoformat(),
        }}
        first_response: httpx.Response = await rpc_request(
            url='/api/v1/reservation',
            method='create_reservation',
            params=first_reservation,
            headers={"Authorization": access_token}
        )
        assert not first_response.json().get('error', None)

        second_reservation = {'reservation': {
            'coworking_id': create_coworking.id, 'place_type': 'meeting_room',
            'session_start': datetime.datetime(2025, 5, 1, 12, 30).isoformat(),
            'session_end': datetime.datetime(2025, 5, 1, 13, 30).isoformat(),
        }}

        second_response: httpx.Response = await rpc_request(
            url='/api/v1/reservation',
            method='create_reservation',
            params=second_reservation,
            headers={"Authorization": access_token}
        )
        json_ = second_response.json()
        assert json_['error']['code'] == -32005

    @pytest.mark.asyncio
    async def test_create_with_full_conflict(
            self,
            rpc_request: Callable,
            access_token: str,
            create_coworking: Coworking,
            create_coworking_seat: CoworkingSeat
    ) -> None:
        first_reservation = {'reservation': {
            'coworking_id': create_coworking.id, 'place_type': 'meeting_room',
            'session_start': datetime.datetime(2025, 5, 1, 13).isoformat(),
            'session_end': datetime.datetime(2025, 5, 1, 14).isoformat(),
        }}
        first_response: httpx.Response = await rpc_request(
            url='/api/v1/reservation',
            method='create_reservation',
            params=first_reservation,
            headers={"Authorization": access_token}
        )
        assert not first_response.json().get('error', None)

        second_reservation = {'reservation': {
            'coworking_id': create_coworking.id, 'place_type': 'meeting_room',
            'session_start': datetime.datetime(2025, 5, 1, 12, 30).isoformat(),
            'session_end': datetime.datetime(2025, 5, 1, 14, 30).isoformat(),
        }}

        second_response: httpx.Response = await rpc_request(
            url='/api/v1/reservation',
            method='create_reservation',
            params=second_reservation,
            headers={"Authorization": access_token}
        )
        json_ = second_response.json()
        assert json_['error']['code'] == -32005

    @pytest.mark.asyncio
    async def test_create_with_full_inner_conflict(
            self,
            rpc_request: Callable,
            access_token: str,
            create_coworking: Coworking,
            create_coworking_seat: CoworkingSeat
    ) -> None:
        first_reservation = {'reservation': {
            'coworking_id': create_coworking.id, 'place_type': 'meeting_room',
            'session_start': datetime.datetime(2025, 5, 1, 12).isoformat(),
            'session_end': datetime.datetime(2025, 5, 1, 14).isoformat(),
        }}
        first_response: httpx.Response = await rpc_request(
            url='/api/v1/reservation',
            method='create_reservation',
            params=first_reservation,
            headers={"Authorization": access_token}
        )
        assert not first_response.json().get('error', None)

        second_reservation = {'reservation': {
            'coworking_id': create_coworking.id, 'place_type': 'meeting_room',
            'session_start': datetime.datetime(2025, 5, 1, 12, 30).isoformat(),
            'session_end': datetime.datetime(2025, 5, 1, 13, 30).isoformat(),
        }}

        second_response: httpx.Response = await rpc_request(
            url='/api/v1/reservation',
            method='create_reservation',
            params=second_reservation,
            headers={"Authorization": access_token}
        )
        json_ = second_response.json()
        assert json_['error']['code'] == -32005

    @pytest.mark.asyncio
    async def test_end_less_than_start(
            self,
            rpc_request: Callable,
            access_token: str,
    ) -> None:
        reservation = {'reservation': {
            'coworking_id': "Random_ID", 'place_type': 'meeting_room',
            'session_start': "2024-05-10 12:00:00",
            'session_end': "2024-05-10 11:00:00",
        }}
        response: httpx.Response = await rpc_request(
            url='/api/v1/reservation',
            method='create_reservation',
            params=reservation,
            headers={"Authorization": access_token}
        )
        json_ = response.json()
        assert json_['error']['code'] == -32602

    @pytest.mark.asyncio
    async def test_unable_create_because_non_business_day(
            self,
            rpc_request: Callable,
            access_token: str,
            create_coworking: Coworking,
            create_coworking_seat: CoworkingSeat,
            create_non_business_day: NonBusinessDay,
    ) -> None:
        reservation = {'reservation': {
            'coworking_id': "Random_ID", 'place_type': 'meeting_room',
            'session_start': "2024-05-10 11:00:00",
            'session_end': "2024-05-10 12:00:00",
        }}
        response: httpx.Response = await rpc_request(
            url='/api/v1/reservation',
            method='create_reservation',
            params=reservation,
            headers={"Authorization": access_token}
        )
        json_ = response.json()
        assert json_['error']['code'] == -32005
