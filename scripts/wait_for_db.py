#!/usr/bin/env python
"""Utility to wait for the configured database to become available."""
from __future__ import annotations

import os
import sys
import time

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError


def _database_uri() -> str | None:
    uri = os.getenv("SQLALCHEMY_DATABASE_URI") or os.getenv("DATABASE_URL")
    if uri:
        return uri
    host = os.getenv("DB_HOST") or os.getenv("POSTGRES_HOST")
    if not host:
        return None
    user = os.getenv("DB_USER", os.getenv("POSTGRES_USER", "postgres"))
    password = os.getenv("DB_PASSWORD", os.getenv("POSTGRES_PASSWORD", "postgres"))
    name = os.getenv("DB_NAME", os.getenv("POSTGRES_DB", "postgres"))
    port = os.getenv("DB_PORT", os.getenv("POSTGRES_PORT", "5432"))
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{name}"


def main() -> int:
    uri = _database_uri()
    if not uri:
        print("[wait_for_db] No database URI configured, skipping wait.")
        return 0

    timeout = int(os.getenv("DB_WAIT_TIMEOUT", "60"))
    interval = float(os.getenv("DB_WAIT_INTERVAL", "2"))
    deadline = time.monotonic() + timeout
    engine = create_engine(uri, pool_pre_ping=True)

    while True:
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            print("[wait_for_db] Database connection established.")
            return 0
        except OperationalError as exc:  # pragma: no cover - runtime guard
            if time.monotonic() >= deadline:
                print(f"[wait_for_db] Database unavailable: {exc}")
                return 1
            print("[wait_for_db] Waiting for database…")
            time.sleep(interval)


if __name__ == "__main__":  # pragma: no cover - script entry point
    sys.exit(main())
