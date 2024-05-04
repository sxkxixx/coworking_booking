FROM python:3.10

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION="1.5.1" \
    PATH="$PATH:/root/.local/bin"

COPY pyproject.toml poetry.lock start.sh ./

RUN curl -sSL https://install.python-poetry.org | python3 - && \
    poetry --version && \
    poetry config virtualenvs.create false && \
    poetry install --without dev --no-interaction --no-ansi

WORKDIR src/

COPY ./src ./

CMD ["/start.sh"]
