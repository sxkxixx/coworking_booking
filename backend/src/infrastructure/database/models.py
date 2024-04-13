from typing import Optional

import peewee

from .db import database
from .enum import OnDelete

__all__ = [
    'User',
    'UserTelegramInfo',
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
