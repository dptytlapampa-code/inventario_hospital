"""Add DNI column with uniqueness to usuarios."""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "f3c92c1f2f6d"
down_revision = "e1d3f9c5c1d5"
branch_labels = None
depends_on = None

usuarios_table = sa.table(
    "usuarios",
    sa.column("id", sa.Integer),
    sa.column("dni", sa.String(length=20)),
)


def upgrade() -> None:
    with op.batch_alter_table("usuarios", schema=None, recreate="always") as batch_op:
        batch_op.add_column(sa.Column("dni", sa.String(length=20), nullable=True))

    bind = op.get_bind()
    results = bind.execute(sa.select(usuarios_table.c.id)).fetchall()
    for (row_id,) in results:
        generated_dni = f"SIN-DNI-{row_id:04d}"
        bind.execute(
            sa.update(usuarios_table)
            .where(usuarios_table.c.id == row_id)
            .values(dni=generated_dni)
        )

    with op.batch_alter_table("usuarios", schema=None, recreate="always") as batch_op:
        batch_op.alter_column("dni", existing_type=sa.String(length=20), nullable=False)
        batch_op.create_unique_constraint("uq_usuario_dni", ["dni"])
        batch_op.create_unique_constraint("uq_usuario_username", ["username"])


def downgrade() -> None:
    with op.batch_alter_table("usuarios", schema=None, recreate="always") as batch_op:
        batch_op.drop_constraint("uq_usuario_username", type_="unique")
        batch_op.drop_constraint("uq_usuario_dni", type_="unique")
        batch_op.drop_column("dni")
