"""Restructure equipo_insumos table to store assignments metadata."""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "4f8bb8f9d71a"
down_revision = "f3c92c1f2f6d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.rename_table("equipo_insumos", "equipo_insumos_old")

    op.create_table(
        "equipo_insumos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("equipo_id", sa.Integer(), nullable=False),
        sa.Column("insumo_id", sa.Integer(), nullable=False),
        sa.Column("cantidad", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "fecha",
            sa.DateTime(timezone=True),
            server_default=sa.func.current_timestamp(),
            nullable=False,
        ),
        sa.Column("comentario", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["equipo_id"], ["equipos.id"], name="fk_equipo_insumos_equipo"),
        sa.ForeignKeyConstraint(["insumo_id"], ["insumos.id"], name="fk_equipo_insumos_insumo"),
        sa.PrimaryKeyConstraint("id", name="pk_equipo_insumos"),
    )

    connection = op.get_bind()
    connection.execute(
        sa.text(
            """
            INSERT INTO equipo_insumos (equipo_id, insumo_id, cantidad, fecha)
            SELECT equipo_id, insumo_id, 1, CURRENT_TIMESTAMP FROM equipo_insumos_old
            """
        )
    )

    op.drop_table("equipo_insumos_old")
    op.alter_column("equipo_insumos", "cantidad", server_default=None)


def downgrade() -> None:
    op.create_table(
        "equipo_insumos_old",
        sa.Column("equipo_id", sa.Integer(), nullable=False),
        sa.Column("insumo_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["equipo_id"], ["equipos.id"], name="equipo_insumos_equipo_id_fkey"),
        sa.ForeignKeyConstraint(["insumo_id"], ["insumos.id"], name="equipo_insumos_insumo_id_fkey"),
        sa.PrimaryKeyConstraint("equipo_id", "insumo_id", name="equipo_insumos_pkey"),
    )

    connection = op.get_bind()
    connection.execute(
        sa.text(
            """
            INSERT INTO equipo_insumos_old (equipo_id, insumo_id)
            SELECT equipo_id, insumo_id
            FROM (
                SELECT
                    equipo_id,
                    insumo_id,
                    ROW_NUMBER() OVER (
                        PARTITION BY equipo_id, insumo_id
                        ORDER BY fecha DESC NULLS LAST, id DESC
                    ) AS rn
                FROM equipo_insumos
            ) ranked
            WHERE rn = 1
            """
        )
    )

    op.drop_table("equipo_insumos")
    op.rename_table("equipo_insumos_old", "equipo_insumos")
