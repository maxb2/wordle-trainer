all: lint test

build:
	@rm -rf dist
	@poetry build

format:
	@poetry run black .

lint:
	@poetry run pylint ./wordle_trainer
	@poetry run black --check .

publish:
	@poetry run twine upload --skip-existing dist/*

test:
	@poetry run pytest --cov=./wordle_trainer

watch:
	@poetry run ptw

.PHONY: build docs test
