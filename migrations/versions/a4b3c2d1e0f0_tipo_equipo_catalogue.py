"""Introduce dynamic equipment type catalogue."""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

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


EQUIPO_TYPE_VALUES = tuple(slug for slug, _ in DEFAULT_TYPES)


def _enum_values_sql(values: tuple[str, ...]) -> str:
    ordered: list[str] = []
    seen: set[str] = set()
    for value in values:
        for candidate in (value, value.upper()):
            if candidate not in seen:
                ordered.append(candidate)
                seen.add(candidate)
    return ", ".join(f"'{value}'" for value in ordered)


def upgrade() -> None:
    op.create_table(
        "tipo_equipo",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slug", sa.String(length=80), nullable=False),
        sa.Column("nombre", sa.String(length=160), nullable=False),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.current_timestamp(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.current_timestamp(),
            nullable=False,
        ),
        sa.UniqueConstraint("slug", name="uq_tipo_equipo_slug"),
        sa.UniqueConstraint("nombre", name="uq_tipo_equipo_nombre"),
    )

    bind = op.get_bind()
    inspector = inspect(bind)

    with op.batch_alter_table("equipos", recreate="always") as batch_op:
        batch_op.add_column(sa.Column("tipo_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_equipos_tipo_equipo",
            "tipo_equipo",
            ["tipo_id"],
            ["id"],
        )

    insert_stmt = sa.text(
        "INSERT INTO tipo_equipo (slug, nombre, activo, created_at, updated_at) "
        "VALUES (:slug, :nombre, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
    )
    for slug, nombre in DEFAULT_TYPES:
        bind.execute(insert_stmt, {"slug": slug, "nombre": nombre})

    update_stmt = sa.text(
        "UPDATE equipos SET tipo_id = (SELECT id FROM tipo_equipo WHERE slug = :slug) "
        "WHERE tipo = :legacy"
    )
    for slug, _ in DEFAULT_TYPES:
        bind.execute(update_stmt, {"slug": slug, "legacy": slug})

    fallback_stmt = sa.text(
        "UPDATE equipos SET tipo_id = (SELECT id FROM tipo_equipo WHERE slug = :slug) "
        "WHERE tipo_id IS NULL"
    )
    bind.execute(fallback_stmt, {"slug": "otro"})

    constraints = {c["name"] for c in inspector.get_check_constraints("equipos")}
    drop_legacy = LEGACY_TYPE_CHECK in constraints

    with op.batch_alter_table("equipos", recreate="always") as batch_op:
        if drop_legacy:
            batch_op.drop_constraint(LEGACY_TYPE_CHECK, type_="check")
        batch_op.alter_column("tipo_id", existing_type=sa.Integer(), nullable=False)
        batch_op.drop_column("tipo")


LEGACY_TYPE_CHECK = "ck_equipos_tipo"


def downgrade() -> None:
    with op.batch_alter_table("equipos", recreate="always") as batch_op:
        batch_op.add_column(sa.Column("tipo", sa.String(length=50), nullable=True))
        batch_op.create_check_constraint(
            LEGACY_TYPE_CHECK,
            f"tipo IN ({_enum_values_sql(EQUIPO_TYPE_VALUES)})",
        )

    bind = op.get_bind()
    rows = bind.execute(
        sa.text(
            "SELECT e.id, COALESCE(te.slug, 'otro') AS slug "
            "FROM equipos e LEFT JOIN tipo_equipo te ON te.id = e.tipo_id"
        )
    ).fetchall()
    update_legacy = sa.text("UPDATE equipos SET tipo = :slug WHERE id = :equipo_id")
    for equipo_id, slug in rows:
        bind.execute(update_legacy, {"slug": slug or "otro", "equipo_id": equipo_id})

    bind.execute(sa.text("UPDATE equipos SET tipo = 'otro' WHERE tipo IS NULL"))

    with op.batch_alter_table("equipos", recreate="always") as batch_op:
        batch_op.alter_column("tipo", existing_type=sa.String(length=50), nullable=False)

    op.drop_constraint("fk_equipos_tipo_equipo", "equipos", type_="foreignkey")

    with op.batch_alter_table("equipos", recreate="always") as batch_op:
        batch_op.drop_column("tipo_id")

    op.drop_table("tipo_equipo")
