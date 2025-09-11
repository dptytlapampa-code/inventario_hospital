import os
from pathlib import Path

from dotenv import load_dotenv

# Load variables from a .env file if present
BASE_DIR = Path(__file__).resolve().parent
load_dotenv()


class Config:
    """Base configuration for the Flask application."""

    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev")
    SQLALCHEMY_DATABASE_URI: str = os.getenv(
        "DATABASE_URL", f"sqlite:///{BASE_DIR / 'app.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
