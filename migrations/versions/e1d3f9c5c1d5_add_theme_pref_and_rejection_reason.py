"""Add user theme preference and rejection reason for licenses."""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "e1d3f9c5c1d5"
down_revision = "d2f6f3b4a1c9"
branch_labels = None
depends_on = None


theme_enum = sa.Enum("light", "dark", "system", name="theme_preference")


def upgrade() -> None:
    bind = op.get_bind()
    theme_enum.create(bind, checkfirst=True)

    op.add_column(
        "usuarios",
        sa.Column(
            "theme_pref",
            theme_enum,
            nullable=False,
            server_default="system",
        ),
    )

    op.add_column("licencias", sa.Column("motivo_rechazo", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("licencias", "motivo_rechazo")

    op.drop_column("usuarios", "theme_pref")

    bind = op.get_bind()
    theme_enum.drop(bind, checkfirst=True)
