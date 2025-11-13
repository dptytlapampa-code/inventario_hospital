#!/bin/bash
set -euo pipefail

export FLASK_APP="${FLASK_APP:-wsgi.py}"

python /app/scripts/wait_for_db.py

flask db upgrade

exec gunicorn --bind 0.0.0.0:5000 --workers "${GUNICORN_WORKERS:-4}" wsgi:app
