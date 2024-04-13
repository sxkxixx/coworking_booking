def asyncpg_uri(
        *,
        user: str,
        password: str,
        host: str,
        port: str,
        database_name: str
):
    return _get_db_uri('postgresql+asyncpg', user, password, host, port, database_name)


def _get_db_uri(
        driver: str,
        user: str,
        password: str,
        host: str,
        port: str,
        database_name: str
) -> str:
    return f'{driver}://{user}:{password}@{host}:{port}/{database_name}'
