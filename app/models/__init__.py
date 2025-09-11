"""Application database models and utilities."""

from flask_sqlalchemy import SQLAlchemy

# Global SQLAlchemy database handle.  This is initialised in
# :func:`app.create_app` and imported by the rest of the application
# modules.  Having a single shared instance keeps the session management
# centralised and makes the models easy to declare.
db = SQLAlchemy()

__all__ = ["db"]
