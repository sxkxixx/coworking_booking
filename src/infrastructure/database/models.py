import datetime
from typing import Optional

import peewee

from .db import database
from .enum import OnDelete, Weekday, PlaceType, BookingStatus
from .fields import CharEnum

__all__ = [
    'User',
    'UserTelegramInfo',
    'Coworking',
    'WorkingSchedule',
    'CoworkingSeat',
    'Reservation'
]


class User(peewee.Model):
    id: str = peewee.CharField(max_length=32, primary_key=True)
    email: str = peewee.CharField(max_length=64, unique=True, null=False)
    hashed_password: str = peewee.CharField(max_length=256, null=False)
    last_name: str = peewee.CharField(max_length=32, null=False)
    first_name: str = peewee.CharField(max_length=32, null=False)
    patronymic: Optional[str] = peewee.CharField(max_length=32, null=True)
    is_student: bool = peewee.BooleanField(null=False)
    avatar_url: Optional[str] = peewee.CharField(max_length=128, null=True)

    class Meta:
        table_name = 'users'
        database = database


class UserTelegramInfo(peewee.Model):
    user: User = peewee.ForeignKeyField(
        User, backref='telegram_info', primary_key=True, on_delete=OnDelete.CASCADE.value
    )
    username: str = peewee.CharField(max_length=64, null=False)
    chat_id: int = peewee.BigIntegerField(null=False)

    class Meta:
        table_name = 'users_telegram_info'
        database = database


class Coworking(peewee.Model):
    id: str = peewee.CharField(max_length=32, primary_key=True)
    title: str = peewee.CharField(max_length=128, null=False)
    institute: str = peewee.CharField(max_length=128, null=False)
    description: str = peewee.CharField(max_length=1024, null=False)
    address: str = peewee.CharField(max_length=128, null=False)

    class Meta:
        table_name = 'coworking_places'
        database = database


class WorkingSchedule(peewee.Model):
    id: int = peewee.IntegerField(primary_key=True)
    coworking: Coworking = peewee.ForeignKeyField(
        Coworking, backref='working_schedules', on_delete=OnDelete.RESTRICT.value
    )
    week_day: Weekday = CharEnum(_enum=Weekday, null=False, max_length=16)
    start_time: datetime.time = peewee.TimeField(formats=['%H:%M:%S'], null=False)
    end_time: datetime.time = peewee.TimeField(formats=['%H:%M:%S'], null=False)
    is_weekend: bool = peewee.BooleanField(null=False)

    class Meta:
        table_name = 'coworking_working_schedule'
        database = database


class CoworkingSeat(peewee.Model):
    id: int = peewee.IntegerField(primary_key=True)
    coworking: Coworking = peewee.ForeignKeyField(Coworking, backref='seats')
    label: Optional[str] = peewee.CharField(max_length=64, null=True)
    description: str = peewee.CharField(max_length=1024, null=False)
    place_type: PlaceType = CharEnum(_enum=PlaceType, max_length=32, null=False)
    seats_count: int = peewee.SmallIntegerField(null=False)

    class Meta:
        table_name = 'coworking_seats'
        database = database


class Reservation(peewee.Model):
    id: int = peewee.BigIntegerField(primary_key=True)
    user: User = peewee.ForeignKeyField(
        User, backref='user_bookings', on_delete=OnDelete.CASCADE.value
    )
    seat: CoworkingSeat = peewee.ForeignKeyField(
        CoworkingSeat, backref='seat_booking', on_delete=OnDelete.CASCADE.value
    )
    session_start: datetime.datetime = peewee.DateTimeField(null=False)
    session_end: datetime.datetime = peewee.DateTimeField(null=False)
    status: BookingStatus = CharEnum(_enum=BookingStatus, default=BookingStatus.NEW, null=False)
    created_at: datetime.datetime = peewee.DateTimeField(default=datetime.datetime.utcnow)
