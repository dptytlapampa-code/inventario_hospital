"""Add user theme preference and rejection reason for licenses."""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "e1d3f9c5c1d5"
down_revision = "d2f6f3b4a1c9"
branch_labels = None
depends_on = None

THEME_VALUES = ("light", "dark", "system", "LIGHT", "DARK", "SYSTEM")


def _enum_values_sql(values: tuple[str, ...]) -> str:
    return ", ".join(f"'{value}'" for value in values)


def upgrade() -> None:
    with op.batch_alter_table("usuarios", recreate="always") as batch_op:
        batch_op.add_column(
            sa.Column(
                "theme_pref",
                sa.String(length=20),
                nullable=False,
                server_default=sa.text("'system'"),
            )
        )
        batch_op.create_check_constraint(
            "ck_usuarios_theme_pref",
            f"theme_pref IN ({_enum_values_sql(THEME_VALUES)})",
        )

    with op.batch_alter_table("usuarios", recreate="always") as batch_op:
        batch_op.alter_column(
            "theme_pref",
            existing_type=sa.String(length=20),
            server_default=None,
        )

    with op.batch_alter_table("licencias", recreate="always") as batch_op:
        batch_op.add_column(sa.Column("motivo_rechazo", sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("licencias", recreate="always") as batch_op:
        batch_op.drop_column("motivo_rechazo")

    with op.batch_alter_table("usuarios", recreate="always") as batch_op:
        batch_op.drop_constraint("ck_usuarios_theme_pref", type_="check")
        batch_op.drop_column("theme_pref")
