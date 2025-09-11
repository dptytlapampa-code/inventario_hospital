"""Simple seed script to load JSON fixtures."""
from __future__ import annotations

import json
from pathlib import Path

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def load_fixtures() -> None:
    """Load every JSON file in the fixtures directory.

    This script does not integrate with a database. It simply demonstrates how
    fixtures might be processed and is intended as a placeholder for real seed
    logic.
    """
    for fixture in FIXTURES_DIR.glob("*.json"):
        data = json.loads(fixture.read_text())
        print(f"Loaded {fixture.name}: {len(data)} records")


if __name__ == "__main__":
    load_fixtures()
