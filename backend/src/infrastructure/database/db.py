from peewee_async import PostgresqlDatabase, Manager

from infrastructure.config import DatabaseSettings

db_settings = DatabaseSettings()

database = PostgresqlDatabase(
    database=db_settings.DATABASE_NAME,
    user=db_settings.DATABASE_USER,
    password=db_settings.DATABASE_PASSWORD,
    host=db_settings.DATABASE_HOST,
    port=db_settings.DATABASE_PORT
)
manager = Manager(database)
