"""Introduce dynamic equipment type catalogue."""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "a4b3c2d1e0f0"
down_revision = "f3c92c1f2f6d"
branch_labels = None
depends_on = None

DEFAULT_TYPES: list[tuple[str, str]] = [
    ("impresora", "Impresora"),
    ("router", "Router"),
    ("switch", "Switch"),
    ("notebook", "Notebook"),
    ("cpu", "CPU"),
    ("monitor", "Monitor"),
    ("access_point", "Access Point"),
    ("scanner", "Scanner"),
    ("proyector", "Proyector"),
    ("telefono_ip", "Teléfono IP"),
    ("ups", "UPS"),
    ("otro", "Otro"),
]


def upgrade() -> None:
    op.create_table(
        "tipo_equipo",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(length=160), nullable=False),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("nombre", name="uq_tipo_equipo_nombre"),
    )
    op.add_column("equipos", sa.Column("tipo_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_equipos_tipo_equipo",
        "equipos",
        "tipo_equipo",
        ["tipo_id"],
        ["id"],
    )

    bind = op.get_bind()
    for slug, nombre in DEFAULT_TYPES:
        bind.execute(
            sa.text("INSERT INTO tipo_equipo (nombre, activo) VALUES (:nombre, true)"),
            {"nombre": nombre},
        )
        bind.execute(
            sa.text(
                "UPDATE equipos SET tipo_id = (SELECT id FROM tipo_equipo WHERE nombre = :nombre) "
                "WHERE tipo = :slug"
            ),
            {"nombre": nombre, "slug": slug},
        )

    # Fallback: asignar tipo "Otro" a cualquier registro sin mapeo previo
    bind.execute(
        sa.text(
            "UPDATE equipos SET tipo_id = (SELECT id FROM tipo_equipo WHERE nombre = :nombre) "
            "WHERE tipo_id IS NULL"
        ),
        {"nombre": "Otro"},
    )

    op.alter_column("equipos", "tipo_id", existing_type=sa.Integer(), nullable=False)
    op.drop_column("equipos", "tipo")
    op.alter_column("tipo_equipo", "activo", existing_type=sa.Boolean(), server_default=None)
    op.execute("DROP TYPE IF EXISTS tipo_equipo")


def downgrade() -> None:
    tipo_enum = sa.Enum(*(slug for slug, _ in DEFAULT_TYPES), name="tipo_equipo")
    tipo_enum.create(op.get_bind())

    op.add_column(
        "equipos",
        sa.Column("tipo", tipo_enum, nullable=True),
    )

    bind = op.get_bind()
    rows = bind.execute(sa.text("SELECT id, nombre FROM tipo_equipo")).fetchall()
    mapping = {nombre.lower(): slug for slug, nombre in DEFAULT_TYPES}
    for tipo_id, nombre in rows:
        slug = mapping.get((nombre or "").lower(), "otro")
        bind.execute(
            sa.text("UPDATE equipos SET tipo = :slug WHERE tipo_id = :tipo_id"),
            {"slug": slug, "tipo_id": tipo_id},
        )

    bind.execute(sa.text("UPDATE equipos SET tipo = :slug WHERE tipo IS NULL"), {"slug": "otro"})

    op.alter_column("equipos", "tipo", existing_type=tipo_enum, nullable=False)
    op.drop_constraint("fk_equipos_tipo_equipo", "equipos", type_="foreignkey")
    op.drop_column("equipos", "tipo_id")
    op.drop_table("tipo_equipo")
*** End Patch
