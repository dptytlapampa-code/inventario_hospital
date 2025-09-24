"""Add apellido column to usuarios.

Revision ID: 8a9f4ce0f1a7
Revises: c28f3d5aa8a9
Create Date: 2025-01-14 00:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "8a9f4ce0f1a7"
down_revision = "c28f3d5aa8a9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("usuarios", sa.Column("apellido", sa.String(length=120), nullable=True))


def downgrade() -> None:
    op.drop_column("usuarios", "apellido")
