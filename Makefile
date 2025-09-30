.PHONY: install run test run-windows

install:
	pip install -r requirements.txt

run:
	flask --app wsgi:app run --debug

test:
	pytest

run-windows:
        pwsh -File scripts/run_server.ps1

run-win:
        cmd /c scripts\run_server.bat
