.PHONY: tests
tests:
	PYTHONPATH="src" poetry run pytest

install-dev:
	poetry install

install-prod:
	poetry install --without dev

run:
	...

build:
	...
