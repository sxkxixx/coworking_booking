import datetime
from typing import Optional
from uuid import uuid4

import peewee

from .db import database
from .enum import OnDelete, Weekday, PlaceType, BookingStatus, PasswordTokenEnum
from .fields import CharEnum, IntegerEnum

__all__ = [
    'User',
    'Coworking',
    'WorkingSchedule',
    'CoworkingSeat',
    'Reservation',
    'CoworkingImages',
    'NonBusinessDay',
    'EmailAuthData',
    'PasswordResetToken'
]


class User(peewee.Model):
    id: str = peewee.CharField(max_length=64, primary_key=True, default=uuid4)
    email: str = peewee.CharField(max_length=64, unique=True)
    hashed_password: str = peewee.CharField(max_length=256, null=False)
    last_name: str = peewee.CharField(max_length=32, null=False)
    first_name: str = peewee.CharField(max_length=32, null=False)
    patronymic: Optional[str] = peewee.CharField(max_length=32, null=True)
    is_student: bool = peewee.BooleanField()
    telegram_chat_id: int = peewee.BigIntegerField(null=True)
    avatar_filename: Optional[str] = peewee.CharField(max_length=128, null=True)

    class Meta:
        table_name = 'users'
        database = database


class Coworking(peewee.Model):
    id: str = peewee.CharField(max_length=64, primary_key=True, default=uuid4)
    avatar: str = peewee.CharField(max_length=64)
    title = peewee.CharField(max_length=128, null=False)
    institute: str = peewee.CharField(max_length=128, null=False)
    description: str = peewee.CharField(max_length=1024, null=False)
    address: str = peewee.CharField(max_length=128, null=False)

    class Meta:
        table_name = 'coworking_places'
        database = database


class WorkingSchedule(peewee.Model):
    id: int = peewee.BigAutoField(primary_key=True)
    coworking: Coworking = peewee.ForeignKeyField(
        Coworking, backref='working_schedules', on_delete=OnDelete.RESTRICT.value
    )
    week_day: Weekday = IntegerEnum(_enum=Weekday, null=False)
    start_time: datetime.time = peewee.TimeField(formats=['%H:%M:%S'], null=False)
    end_time: datetime.time = peewee.TimeField(formats=['%H:%M:%S'], null=False)

    class Meta:
        table_name = 'coworking_working_schedule'
        database = database


class CoworkingSeat(peewee.Model):
    id: int = peewee.BigAutoField(primary_key=True)
    coworking: Coworking = peewee.ForeignKeyField(Coworking, backref='seats')
    label: Optional[str] = peewee.CharField(max_length=64, null=True)
    description: str = peewee.CharField(max_length=1024, null=False)
    place_type: PlaceType = CharEnum(_enum=PlaceType, max_length=32, null=False)
    seats_count: int = peewee.SmallIntegerField()

    class Meta:
        table_name = 'coworking_seats'
        database = database


class Reservation(peewee.Model):
    id = peewee.BigAutoField(primary_key=True)
    user: User = peewee.ForeignKeyField(
        User, backref='user_bookings', on_delete=OnDelete.CASCADE.value
    )
    seat: CoworkingSeat = peewee.ForeignKeyField(
        CoworkingSeat, backref='seat_booking', on_delete=OnDelete.CASCADE.value
    )
    session_start = peewee.DateTimeField(null=False)
    session_end = peewee.DateTimeField(null=False)
    status: BookingStatus = CharEnum(_enum=BookingStatus, null=False)
    created_at: datetime.datetime = peewee.DateTimeField(default=datetime.datetime.utcnow)

    class Meta:
        table_name = 'seats_reservations'
        database = database


class CoworkingImages(peewee.Model):
    id = peewee.IntegerField(primary_key=True)
    coworking: Coworking = peewee.ForeignKeyField(
        Coworking, null=False, on_delete=OnDelete.CASCADE.value, backref='images'
    )
    image_filename = peewee.CharField(max_length=64, null=False)

    class Meta:
        table_name = 'coworking_images'
        database = database


class NonBusinessDay(peewee.Model):
    id = peewee.BigAutoField(primary_key=True)
    coworking: Coworking = peewee.ForeignKeyField(
        Coworking, null=False, on_delete=OnDelete.CASCADE.value, backref='days_off'
    )
    day = peewee.DateField(null=False)
    reason: Optional[str] = peewee.CharField(null=True, max_length=512)

    class Meta:
        table_name = 'coworking_non_business_days'
        database = database


class EmailAuthData(peewee.Model):
    id: int = peewee.BigAutoField(primary_key=True)
    user: User = peewee.ForeignKeyField(User, backref='bot_auths')
    password: int = peewee.IntegerField()
    created_at: datetime = peewee.DateTimeField(default=datetime.datetime.utcnow)

    class Meta:
        table_name = 'email_auth_data'
        database = database


class PasswordResetToken(peewee.Model):
    id: str = peewee.CharField(max_length=64, primary_key=True, default=uuid4)
    user: User = peewee.ForeignKeyField(User, backref='password_reset')
    fingerprint: str = peewee.CharField(max_length=128)
    created_at: datetime.datetime = peewee.DateTimeField(default=datetime.datetime.utcnow)
    status = CharEnum(_enum=PasswordTokenEnum, default=PasswordTokenEnum.NEW)

    class Meta:
        table_name = 'password_reset_tokens'
        database = database
