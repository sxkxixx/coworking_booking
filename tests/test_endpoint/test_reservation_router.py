import datetime
import logging
from typing import Callable, Any, Dict

import httpx
import pytest
import pytest_asyncio
from peewee_async import Manager

from infrastructure.database import PlaceType
from infrastructure.database.enum import BookingStatus
from infrastructure.database.models import Coworking, CoworkingSeat, CoworkingEvent, Reservation, \
    User


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
) -> CoworkingEvent:
    return await db_manager.create(
        CoworkingEvent,
        coworking=create_coworking,
        date=datetime.date(2024, 5, 10),
        name="null",
        description="null",
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
            create_non_business_day: CoworkingEvent,
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

    @pytest.mark.asyncio
    async def test_booking_with_two_places(
            self,
            rpc_request: Callable,
            access_token: str,
            db_manager: Manager,
    ) -> None:
        coworking: Coworking = await db_manager.create(
            Coworking,
            title="Антресоли", institute="ГУК", description="description", address="Мира, 19",
        )
        await db_manager.create(
            CoworkingSeat, coworking=coworking, label="Table_1_1",
            description="Description", place_type=PlaceType.TABLE, seats_count=1,
        )
        await db_manager.create(
            CoworkingSeat, coworking=coworking, label="Table_1_2",
            description="Description", place_type=PlaceType.TABLE, seats_count=1,
        )
        response: httpx.Response = await rpc_request(
            url='/api/v1/reservation',
            method='create_reservation',
            params={'reservation': {
                'coworking_id': coworking.id,
                'session_start': "2024-05-10 11:00:00",
                'session_end': "2024-05-10 12:00:00",
                'place_type': PlaceType.TABLE.value,
            }},
            headers={"Authorization": access_token}
        )
        json_ = response.json()
        assert json_.get('error', None) is None
        assert json_['result']['id']

        response: httpx.Response = await rpc_request(
            url='/api/v1/reservation',
            method='create_reservation',
            params={'reservation': {
                'coworking_id': coworking.id,
                'session_start': "2024-05-10 11:00:00",
                'session_end': "2024-05-10 12:00:00",
                'place_type': PlaceType.TABLE.value,
            }},
            headers={"Authorization": access_token}
        )
        json_ = response.json()
        assert json_.get('error', None) is None
        assert json_['result']['id']

    @pytest.mark.asyncio
    async def test_booking_with_one_place(
            self,
            rpc_request: Callable,
            access_token: str,
            db_manager: Manager,
    ) -> None:
        coworking: Coworking = await db_manager.create(
            Coworking,
            title="Антресоли", institute="ГУК", description="description", address="Мира, 19",
        )
        await db_manager.create(
            CoworkingSeat, coworking=coworking, label="Table_1_1",
            description="Description", place_type=PlaceType.TABLE, seats_count=1,
        )

        response: httpx.Response = await rpc_request(
            url='/api/v1/reservation',
            method='create_reservation',
            params={'reservation': {
                'coworking_id': coworking.id,
                'session_start': "2024-05-10 11:00:00",
                'session_end': "2024-05-10 12:00:00",
                'place_type': PlaceType.TABLE.value,
            }},
            headers={"Authorization": access_token}
        )
        json_ = response.json()
        assert json_.get('result')

    @pytest.mark.asyncio
    async def test_booking_no_place_with_need_place_type(
            self,
            rpc_request: Callable,
            access_token: str,
            db_manager: Manager,
    ) -> None:
        coworking: Coworking = await db_manager.create(
            Coworking,
            title="Антресоли", institute="ГУК", description="description", address="Мира, 19",
        )
        await db_manager.create(
            CoworkingSeat, coworking=coworking, label="Table_1_1",
            description="Description", place_type=PlaceType.MEETING_ROOM, seats_count=1,
        )
        response: httpx.Response = await rpc_request(
            url='/api/v1/reservation',
            method='create_reservation',
            params={'reservation': {
                'coworking_id': coworking.id,
                'session_start': "2024-05-10 11:00:00",
                'session_end': "2024-05-10 12:00:00",
                'place_type': PlaceType.TABLE.value,
            }},
            headers={"Authorization": access_token}
        )
        json_ = response.json()
        assert json_.get('error')
        assert json_['error']['code'] == -32005

    @pytest.mark.asyncio
    async def test_not_allowed_because_event(
            self,
            rpc_request: Callable,
            db_manager: Manager,
            access_token: str,
    ) -> None:
        coworking: Coworking = await db_manager.create(
            Coworking,
            title="Антресоли", institute="ГУК", description="description", address="Мира, 19",
        )
        await db_manager.create(
            CoworkingSeat, coworking=coworking, label="Table_1_1",
            description="Description", place_type=PlaceType.MEETING_ROOM, seats_count=1,
        )
        await db_manager.create(
            CoworkingEvent,
            coworking=coworking,
            date=datetime.date.today(),
            name="Event",
            description="Event_Description",
        )
        session_start = datetime.datetime.utcnow()
        session_end = session_start + datetime.timedelta(hours=1)
        response: httpx.Response = await rpc_request(
            url='/api/v1/reservation',
            method='create_reservation',
            params={'reservation': {
                'coworking_id': coworking.id,
                'session_start': session_start.isoformat(),
                'session_end': session_end.isoformat(),
                'place_type': PlaceType.TABLE.value,
            }},
            headers={"Authorization": access_token}
        )
        json_ = response.json()
        assert json_.get('error')
        assert json_['error']['code'] == -32005, json_

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        'delta',
        [
            datetime.timedelta(minutes=30),
            datetime.timedelta(minutes=-30),
        ]
    )
    async def test_with_user_reservations_conflict(
            self,
            rpc_request: Callable,
            db_manager: Manager,
            access_token: str,
            delta: datetime.timedelta,
    ) -> None:
        coworking: Coworking = await db_manager.create(
            Coworking,
            title="Антресоли", institute="ГУК", description="description", address="Мира, 19",
        )
        await db_manager.create(
            CoworkingSeat, coworking=coworking, label="Table_1_1",
            description="Description", place_type=PlaceType.MEETING_ROOM, seats_count=1,
        )
        await db_manager.create(
            CoworkingSeat, coworking=coworking, label="Table", description="sadadsd",
            place_type=PlaceType.MEETING_ROOM, seats_count=1,
        )
        session_start = datetime.datetime.now()
        session_end = session_start + datetime.timedelta(hours=1)
        response: httpx.Response = await rpc_request(
            url='/api/v1/reservation',
            method='create_reservation',
            params={'reservation': {
                'coworking_id': coworking.id, 'session_start': session_start.isoformat(),
                'session_end': session_end.isoformat(), 'place_type': PlaceType.MEETING_ROOM.value,
            }},
            headers={"Authorization": access_token}
        )
        json_: Dict[str, Any] = response.json()
        assert json_.get('error') is None

        session_start += delta
        session_end += delta

        response: httpx.Response = await rpc_request(
            url='/api/v1/reservation',
            method='create_reservation',
            params={'reservation': {
                'coworking_id': coworking.id, 'session_start': session_start.isoformat(),
                'session_end': session_end.isoformat(), 'place_type': PlaceType.MEETING_ROOM.value,
            }},
            headers={"Authorization": access_token}
        )
        json_ = response.json()
        assert json_['error']['code'] == -32005


class TestCancelReservation:
    @pytest.mark.asyncio
    async def test_reservation_not_exists(
            self,
            rpc_request: Callable,
            access_token: str,
    ) -> None:
        response: httpx.Response = await rpc_request(
            url='/api/v1/reservation',
            method="cancel_reservation",
            params={"reservation_id": 1},
            headers={"Authorization": access_token},
        )
        json_: Dict[str, Any] = response.json()
        assert json_.get('error')
        assert json_.get('error')["code"] == -32005, json_

    @pytest.mark.asyncio
    async def test_cancel_passed_reservation(
            self,
            rpc_request: Callable,
            access_token: str,
            db_manager: Manager,
            registered_user: Dict[str, Any]
    ) -> None:
        coworking: Coworking = await db_manager.create(
            Coworking, title="a", institute="a", description="a", address="a",
        )
        seat: CoworkingSeat = await db_manager.create(
            CoworkingSeat, coworking=coworking, place_type=PlaceType.TABLE, seats_count=1,
        )
        reservation: Reservation = await db_manager.create(
            Reservation,
            user_id=registered_user["id"],
            seat=seat,
            session_start=datetime.datetime(2024, 6, 7, 10),
            session_end=datetime.datetime(2024, 6, 7, 12),
            status=BookingStatus.PASSED,
        )
        response: httpx.Response = await rpc_request(
            url="/api/v1/reservation",
            method="cancel_reservation",
            params={"reservation_id": reservation.id},
            headers={"Authorization": access_token},
        )
        json_: Dict[str, Any] = response.json()
        assert json_.get('error')
        assert json_['error']['code'] == -32005

    @pytest.mark.asyncio
    async def test_cancel_another_user_reservation(
            self,
            db_manager: Manager,
            rpc_request: Callable,
            access_token: str,
    ) -> None:
        user: User = await db_manager.create(
            User,
            email="name.surname@urfu.me",
            hashed_password="password",
            last_name="Surname",
            first_name="Name",
            is_student=True,
        )
        coworking: Coworking = await db_manager.create(
            Coworking,
            title="a", institute="a",
            description="a", address="a",
        )
        seat: CoworkingSeat = await db_manager.create(
            CoworkingSeat,
            coworking=coworking,
            place_type=PlaceType.TABLE,
            seats_count=1,
        )
        reservation: Reservation = await db_manager.create(
            Reservation,
            user=user,
            seat=seat,
            session_start=datetime.datetime(2024, 6, 7, 10),
            session_end=datetime.datetime(2024, 6, 7, 12),
            status=BookingStatus.PASSED,
        )
        response: httpx.Response = await rpc_request(
            url="/api/v1/reservation",
            method="cancel_reservation",
            params={"reservation_id": reservation.id},
            headers={"Authorization": access_token},
        )
        json_: Dict[str, Any] = response.json()
        assert json_['error']['code'] == -32005

    @pytest.mark.asyncio
    async def test_cancel_already_cancelled(
            self,
            db_manager: Manager,
            rpc_request: Callable,
            access_token: str,
            registered_user: Dict[str, Any],
    ) -> None:
        coworking: Coworking = await db_manager.create(
            Coworking, title="a", institute="a", description="a", address="a",
        )
        seat: CoworkingSeat = await db_manager.create(
            CoworkingSeat, coworking=coworking, place_type=PlaceType.TABLE, seats_count=1,
        )
        reservation: Reservation = await db_manager.create(
            Reservation,
            user_id=registered_user["id"],
            seat=seat,
            session_start=datetime.datetime(2024, 6, 7, 10),
            session_end=datetime.datetime(2024, 6, 7, 12),
            status=BookingStatus.PASSED,
        )
        response: httpx.Response = await rpc_request(
            url="/api/v1/reservation",
            method="cancel_reservation",
            params={"reservation_id": reservation.id},
            headers={"Authorization": access_token},
        )
        json_: Dict[str, Any] = response.json()
        assert json_['error']['code'] == -32005

    @pytest.mark.asyncio
    async def test_successful_cancel(
            self,
            db_manager: Manager,
            registered_user: Dict[str, Any],
            access_token: str,
            rpc_request: Callable
    ) -> None:
        coworking: Coworking = await db_manager.create(
            Coworking, title="a", institute="a", description="a", address="a",
        )
        seat: CoworkingSeat = await db_manager.create(
            CoworkingSeat, coworking=coworking, place_type=PlaceType.TABLE,
            seats_count=1,
        )
        reservation: Reservation = await db_manager.create(
            Reservation,
            user_id=registered_user["id"],
            seat=seat,
            session_start=datetime.datetime(2024, 6, 7, 10),
            session_end=datetime.datetime(2024, 6, 7, 12),
            status=BookingStatus.CONFIRMED,
        )
        response: httpx.Response = await rpc_request(
            url="/api/v1/reservation",
            method="cancel_reservation",
            params={"reservation_id": reservation.id},
            headers={"Authorization": access_token},
        )
        json_ = response.json()
        assert json_["result"] is None
        booking: Reservation = await db_manager.get(
            Reservation, Reservation.id == reservation.id
        )
        assert booking.status == BookingStatus.CANCELLED
