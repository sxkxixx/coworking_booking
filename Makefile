.PHONY: tests
tests:
	PYTHONPATH="src" poetry run pytest

install-dev:
	poetry install

install-prod:
	poetry install --without dev

build:
	docker build . -t coworking_booking_api

run:
	docker run --env-file .env coworking_booking_api
