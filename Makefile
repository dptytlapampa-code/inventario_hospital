.PHONY: install run test

install:
	pip install -r requirements.txt

run:
	flask --app wsgi:app run --debug

test:
	pytest
