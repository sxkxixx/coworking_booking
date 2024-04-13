FROM python:3.10

WORKDIR src/

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY ../tests .

RUN curl -sSL https://install.python-poetry.org | python3 -

ENV PATH="$PATH:/root/.local/bin"

RUN poetry config virtualenvs.create false && \
    poetry install --without dev --no-interaction --no-ansi

CMD ls && python3 main.py
