import asyncio

import pytest
import pytest_asyncio
from peewee_async import PostgresqlDatabase, Manager

from infrastructure.config import DatabaseSettings
from infrastructure.database.models import *

database_models = [
    User,
    Coworking,
    WorkingSchedule,
    CoworkingSeat,
    Reservation,
    CoworkingImages,
    NonBusinessDay,
    EmailAuthData,
    PasswordResetToken,
]


@pytest_asyncio.fixture(scope='session', autouse=True)
async def event_loop():
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop


@pytest.fixture(scope='session')
def db_settings() -> DatabaseSettings:
    return DatabaseSettings()


@pytest.fixture(scope='session', autouse=True)
def db_manager(db_settings: DatabaseSettings) -> Manager:
    database = PostgresqlDatabase(
        database=db_settings.DATABASE_NAME,
        user=db_settings.DATABASE_USER,
        password=db_settings.DATABASE_PASSWORD,
        host=db_settings.DATABASE_HOST,
        port=db_settings.DATABASE_PORT
    )
    database.set_allow_sync(False)
    manager = Manager(database=database)
    with manager.allow_sync():
        for model in database_models:
            model._meta.database = database
            model.create_table()
    return manager


@pytest.fixture(scope='function', autouse=True)
def truncate_tables(db_manager: Manager):
    yield
    with db_manager.allow_sync():
        for model in database_models:
            model.truncate_table(cascade=True)
