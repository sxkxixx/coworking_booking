import logging
import os
from datetime import datetime, date
from typing import Callable, Dict, Any

import httpx
import pytest
from peewee_async import Manager

from infrastructure.database import (
    Coworking,
    CoworkingSeat,
    User,
    Reservation,
    CoworkingEvent,
    WorkingSchedule
)
from infrastructure.database.enum import PlaceType, BookingStatus

coworking_url = "/api/v1/coworking"


class TestGetCoworkingById:
    @pytest.mark.asyncio
    async def test_coworking_not_exists(self, rpc_request: Callable) -> None:
        random_id = os.urandom(16).hex()
        response: httpx.Response = await rpc_request(
            url=coworking_url, method="get_coworking", params={"coworking_id": random_id}
        )
        _json = response.json()
        error = _json.get("error")
        assert error["code"] == -32008, _json


class TestGetCoworkingByTimestampRange:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "input_from, input_to",
        [
            ("2024-05-20T10:30:00", "2024-05-20T12:30:00"),
            ("2024-05-20T10:00:00", "2024-05-20T12:16:00"),
            ("2024-05-20T10:00:00", "2024-05-20T10:01:00"),
            ("2024-05-20T00:00:00", "2024-05-20T01:00:00"),
            ("2024-05-20T19:30:00", "2024-05-20T20:30:00"),
            ("2024-05-20T23:30:00", "2024-05-20T23:59:00")
        ]
    )
    async def test_no_any_coworking(
            self,
            rpc_request: Callable,
            input_from: str,
            input_to: str,
    ) -> None:
        """
        Тестирует, что, если коворкингов нет, то список будет пустым на любое время
        """
        interval = {"from": input_from, "to": input_to}
        response: httpx.Response = await rpc_request(
            url=coworking_url, method="available_coworking_by_timestamp",
            params={"interval": interval}
        )
        json_ = response.json()
        assert len(json_["result"]) == 0

    @pytest.mark.asyncio
    async def test_from_gte_than_to(self, rpc_request: Callable) -> None:
        """
        Проверяет, что сработает валидация, поскольку конец интервала не больше чем начал
        """
        interval = {"from": "2024-05-20T12:30:00", "to": "2024-05-20T11:30:00"}
        response: httpx.Response = await rpc_request(
            url=coworking_url, method="available_coworking_by_timestamp",
            params={"interval": interval}
        )
        json_ = response.json()
        assert json_["error"]["code"] == -32602

    @pytest.mark.asyncio
    async def test_dates_are_not_equals(self, rpc_request: Callable) -> None:
        """
        Проверяет, что сработает валидация, поскольку даты в интервале различаются по дню
        """
        interval = {"from": "2024-05-21T11:30:00", "to": "2024-05-20T12:30:00"}
        response: httpx.Response = await rpc_request(
            url=coworking_url, method="available_coworking_by_timestamp",
            params={"interval": interval}
        )
        json_ = response.json()
        assert json_["error"]["code"] == -32602

    @pytest.mark.asyncio
    async def test_with_correct_timestamp_range_no_conflict(
            self,
            rpc_request: Callable,
            db_manager: Manager
    ) -> None:
        """
        Тестирует, что список коворкингов не будет пуст,
        потому нет временного конфликта
        """
        coworking_id = os.urandom(16).hex()
        interval = {"from": "2024-05-20T12:30:00", "to": "2024-05-20T13:30:00"}
        user: User = await db_manager.create(
            User,
            email="correct@urfu.me",
            hashed_password="hashed_pwd",
            last_name="Surname",
            first_name="Name",
            is_student=True,
        )
        coworking: Coworking = await db_manager.create(
            Coworking, avatar="image.png", title="Title", id=coworking_id,
            institute="IRIT RTF", description="Description", address="Mira 32",
        )
        seat: CoworkingSeat = await db_manager.create(
            CoworkingSeat, coworking=coworking, label="Переговорная 1",
            description="Описание места",
            place_type=PlaceType.MEETING_ROOM, seats_count=15,
        )
        await db_manager.create(
            Reservation,
            user=user,
            seat=seat,
            session_start=datetime(2024, 5, 20, 10),
            session_end=datetime(2024, 5, 20, 12),
            status=BookingStatus.NEW
        )

        response: httpx.Response = await rpc_request(
            url=coworking_url,
            method="available_coworking_by_timestamp",
            params={"interval": interval}
        )
        json_ = response.json()
        result = json_["result"]
        assert len(result) == 1
        assert result[0]["id"] == coworking_id == coworking.id

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "input_from, input_to, session_start, session_end", [
            (
                    "2024-05-20T12:30:00", "2024-05-20T13:30:00",
                    datetime(2024, 5, 20, 12), datetime(2024, 5, 20, 13)
            ),
            (
                    "2024-05-20T12:00:00", "2024-05-20T13:00:00",
                    datetime(2024, 5, 20, 12), datetime(2024, 5, 20, 13)
            ),
            (
                    "2024-05-20T12:30:00", "2024-05-20T13:30:00",
                    datetime(2024, 5, 20, 13), datetime(2024, 5, 20, 14)
            ),
        ]
    )
    async def test_with_correct_timestamp_range_and_conflict(
            self,
            rpc_request: Callable,
            db_manager: Manager,
            input_from: str,
            input_to: str,
            session_start: datetime,
            session_end: datetime,
    ) -> None:
        """Проверяет, что в случае временного конфликта список коворкингов будет пуст"""
        interval = {"from": input_from, "to": input_to}
        user: User = await db_manager.create(
            User,
            email="correct@urfu.me",
            hashed_password="hashed_pwd",
            last_name="Surname",
            first_name="Name",
            is_student=True,
        )
        coworking: Coworking = await db_manager.create(
            Coworking, avatar="image.png", title="Title",
            institute="IRIT RTF", description="Description", address="Mira 32",
        )
        seat: CoworkingSeat = await db_manager.create(
            CoworkingSeat, coworking=coworking, label="Переговорная 1",
            description="Описание места",
            place_type=PlaceType.MEETING_ROOM, seats_count=15,
        )
        await db_manager.create(
            Reservation,
            user=user,
            seat=seat,
            session_start=session_start,
            session_end=session_end,
            status=BookingStatus.CONFIRMED
        )

        response: httpx.Response = await rpc_request(
            url=coworking_url,
            method="available_coworking_by_timestamp",
            params={"interval": interval}
        )
        json_ = response.json()
        result = json_["result"]
        assert len(result) == 0, json_

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "input_from, input_to, session_start, session_end",
        [
            (
                    "2024-05-20T12:00:00", "2024-05-20T13:00:00",
                    datetime(2024, 5, 20, 12, 30), datetime(2024, 5, 20, 13, 30)
            ),
            (
                    "2024-05-20T12:00:00", "2024-05-20T13:00:00",
                    datetime(2024, 5, 20, 11, 30), datetime(2024, 5, 20, 12, 30)
            ),
            (
                    "2024-05-20T12:00:00", "2024-05-20T13:00:00",
                    datetime(2024, 5, 20, 12, 00), datetime(2024, 5, 20, 13, 00)
            )
        ]
    )
    async def test_cancelled_booking_is_no_conflict(
            self,
            rpc_request: Callable,
            db_manager: Manager,
            input_from: str,
            input_to: str,
            session_start: datetime,
            session_end: datetime,
    ) -> None:
        """
        Проверяется,
        что в случае временного конфликта бронирования со статусом CANCELLED не учитывается
        """
        interval = {"from": input_from, "to": input_to}
        user: User = await db_manager.create(
            User,
            email="correct@urfu.me",
            hashed_password="hashed_pwd",
            last_name="Surname",
            first_name="Name",
            is_student=True,
        )
        coworking: Coworking = await db_manager.create(
            Coworking, avatar="image.png", title="Title",
            institute="IRIT RTF", description="Description", address="Mira 32",
        )
        seat: CoworkingSeat = await db_manager.create(
            CoworkingSeat, coworking=coworking, label="Переговорная 1",
            description="Описание места",
            place_type=PlaceType.MEETING_ROOM, seats_count=15,
        )
        await db_manager.create(
            Reservation,
            user=user,
            seat=seat,
            session_start=session_start,
            session_end=session_end,
            status=BookingStatus.CANCELLED
        )

        response: httpx.Response = await rpc_request(
            url=coworking_url,
            method="available_coworking_by_timestamp",
            params={"interval": interval}
        )
        json_ = response.json()
        result = json_["result"]
        assert len(result) == 1, json_

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "input_from, input_to, session_start_1, session_end_1, session_start_2, session_end_2",
        [
            (
                    "2024-05-20T14:00:00",
                    "2024-05-20T15:00:00",
                    datetime(2024, 5, 20, 12),
                    datetime(2024, 5, 20, 13),
                    datetime(2024, 5, 20, 16),
                    datetime(2024, 5, 20, 17)
            ),
            (
                    "2024-05-20T14:00:00",
                    "2024-05-20T15:00:00",
                    datetime(2024, 5, 20, 13),
                    datetime(2024, 5, 20, 13, 59),
                    datetime(2024, 5, 20, 15, 1),
                    datetime(2024, 5, 20, 16)
            ),
            (
                    "2024-05-20T14:00:00",
                    "2024-05-20T15:00:00",
                    datetime(2024, 5, 20, 13),
                    datetime(2024, 5, 20, 14),
                    datetime(2024, 5, 20, 15),
                    datetime(2024, 5, 20, 16)
            ),
        ]
    )
    async def test_with_two_reservation_no_conflict(
            self,
            rpc_request: Callable,
            db_manager: Manager,
            input_from: str,
            input_to: str,
            session_start_1: datetime,
            session_end_1: datetime,
            session_start_2: datetime,
            session_end_2: datetime,
    ) -> None:
        """
        Тестируется правильность фильтрации по времени с двумя бронированиями
        """
        interval = {"from": input_from, "to": input_to}
        user: User = await db_manager.create(
            User,
            email="correct@urfu.me",
            hashed_password="hashed_pwd",
            last_name="Surname",
            first_name="Name",
            is_student=True,
        )
        coworking: Coworking = await db_manager.create(
            Coworking, avatar="image.png", title="Title", id=os.urandom(16).hex(),
            institute="IRIT RTF", description="Description", address="Mira 32",
        )
        seat: CoworkingSeat = await db_manager.create(
            CoworkingSeat, coworking=coworking, label="Переговорная 1",
            description="Описание места",
            place_type=PlaceType.MEETING_ROOM, seats_count=15,
        )
        await db_manager.create(
            Reservation,
            user=user,
            seat=seat,
            session_start=session_start_1,
            session_end=session_end_1,
            status=BookingStatus.NEW
        )
        await db_manager.create(
            Reservation,
            user=user,
            seat=seat,
            session_start=session_start_2,
            session_end=session_end_2,
            status=BookingStatus.NEW
        )

        response: httpx.Response = await rpc_request(
            url=coworking_url,
            method="available_coworking_by_timestamp",
            params={"interval": interval}
        )
        json_ = response.json()
        logging.info(json_)
        result = json_["result"]
        assert len(result) == 1, result
        assert result[0]["id"] == coworking.id

    @pytest.mark.asyncio
    async def test_with_non_working_day(self, rpc_request: Callable, db_manager: Manager) -> None:
        """
        Тестирует, что наличие NonBusinessDay на запрашиваемую дата исключит из списка коворкинг
        """
        coworking: Coworking = await db_manager.create(
            Coworking, avatar="image.png", title="Title", id=os.urandom(16).hex(),
            institute="IRIT RTF", description="Description", address="Mira 32",
        )
        await db_manager.create(
            CoworkingEvent,
            coworking=coworking, date=date(2024, 5, 20), name="null",
        )
        interval = {"from": "2024-05-20T14:00:00", "to": "2024-05-20T15:00:00"}
        response: httpx.Response = await rpc_request(
            url=coworking_url,
            method="available_coworking_by_timestamp",
            params={"interval": interval}
        )
        json_ = response.json()
        assert len(json_["result"]) == 0

    @pytest.mark.asyncio
    async def test_with_out_of_working_schedule(
            self,
            rpc_request: Callable,
            db_manager: Manager
    ) -> None:
        """
        Тестирует, что наличие NonBusinessDay на запрашиваемую дата исключит из списка коворкинг
        """
        coworking: Coworking = await db_manager.create(
            Coworking, avatar="image.png", title="Title", id=os.urandom(16).hex(),
            institute="IRIT RTF", description="Description", address="Mira 32",
        )
        await db_manager.create(
            WorkingSchedule,
            coworking=coworking,
            week_day=0,
            start_time=datetime(2024, 5, 20, 12),
            end_time=datetime(2024, 5, 20, 16),
        )
        left_interval = {"from": "2024-05-20T10:00:00", "to": "2024-05-20T11:00:00"}
        response: httpx.Response = await rpc_request(
            url=coworking_url,
            method="available_coworking_by_timestamp",
            params={"interval": left_interval}
        )
        json_ = response.json()
        assert len(json_["result"]) == 0

        right_interval = {"from": "2024-05-20T17:00:00", "to": "2024-05-20T18:00:00"}
        response: httpx.Response = await rpc_request(
            url=coworking_url,
            method="available_coworking_by_timestamp",
            params={"interval": right_interval}
        )
        json_ = response.json()
        assert len(json_["result"]) == 0


class TestSearchCoworking:
    @pytest.mark.asyncio
    async def test_no_coworkings(self, rpc_request: Callable) -> None:
        response: httpx.Response = await rpc_request(
            url=coworking_url,
            method="get_coworking_by_search_params",
            params={"search": {"title": "коворкинг"}},
        )
        json_: Dict[str, Any] = response.json()
        assert json_.get("error", None) is None
        assert len(json_["result"]) == 0

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "title",
        [
            "радиоточка",
            "РАДИОТОЧКА",
            "рАдИоТоЧкА",
            "РаДио",
            "ТОЧка",
            "диоточ",
        ]
    )
    async def test_search_radiotochka_by_title(
            self,
            rpc_request: Callable,
            db_manager: Manager,
            title: str,
    ) -> None:
        await db_manager.create(
            Coworking,
            title="Радиоточка",
            institute="ИРИТ РТФ",
            description="Описание радиоточки",
            address="ул. Мира, д. 32",
        )
        response: httpx.Response = await rpc_request(
            url=coworking_url,
            method="get_coworking_by_search_params",
            params={"search": {"title": title}}
        )
        json_: Dict[str, Any] = response.json()
        assert json_.get("error", None) is None
        assert len(json_["result"]) == 1

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "institute",
        [
            "ирит",
            "ртф",
            "ирит ртф",
            "ИРИТ РТФ",
        ]
    )
    async def test_search_by_institute(
            self,
            rpc_request: Callable,
            db_manager: Manager,
            institute: str
    ) -> None:
        await db_manager.create(
            Coworking,
            title="Радиоточка",
            institute="ИРИТ РТФ",
            description="Описание радиоточки",
            address="ул. Мира, д. 32",
        )
        response: httpx.Response = await rpc_request(
            url=coworking_url,
            method="get_coworking_by_search_params",
            params={"search": {"institute": institute}}
        )
        json_: Dict[str, Any] = response.json()
        assert json_.get("error", None) is None
        assert len(json_["result"]) == 1

    @pytest.mark.asyncio
    async def test_result_search_is_empty(
            self,
            rpc_request: Callable,
            db_manager: Manager,
    ) -> None:
        await db_manager.create(
            Coworking,
            title="Радиоточка",
            institute="ИРИТ РТФ",
            description="Описание радиоточки",
            address="ул. Мира, д. 32",
        )
        search_queries = [
            "Антресоли", "антресоли", "FYNHTCJKB",
            "Территория интеллектуального роста", "РОСТА",
            "Катушка", "кАТУШКА"
        ]
        for title in search_queries:
            response: httpx.Response = await rpc_request(
                url=coworking_url,
                method="get_coworking_by_search_params",
                params={"search": {"title": title}}
            )
            json_: Dict[str, Any] = response.json()
            assert len(json_["result"]) == 0
