"""Add observaciones column and new estado for equipos."""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0004_equipos_observaciones_en_taller"
down_revision = "0003_insumo_series_equipo_insumos"
branch_labels = None
depends_on = None


ESTADO_VALUES = ("operativo", "servicio_tecnico", "de_baja", "prestado")
NEW_ESTADO = "en_taller"


def _add_enum_value() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TYPE estado_equipo ADD VALUE IF NOT EXISTS '%s'" % NEW_ESTADO)


def _insert_catalog_state() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    for table_name in inspector.get_table_names():
        if "estado" not in table_name or "equipo" not in table_name:
            continue
        columns = inspector.get_columns(table_name)
        column_names = {col["name"]: col for col in columns}
        insert_data: dict[str, object] = {}
        if "nombre" in column_names:
            insert_data["nombre"] = "En taller"
        if "slug" in column_names:
            insert_data["slug"] = NEW_ESTADO
        if "valor" in column_names and "nombre" not in insert_data:
            insert_data["valor"] = NEW_ESTADO
        if not insert_data:
            continue
        non_nullable = {
            name
            for name, col in column_names.items()
            if not col.get("nullable", True)
            and col.get("default") is None
            and col.get("server_default") is None
            and name not in {"id", "created_at", "updated_at"}
        }
        if not non_nullable.issubset(set(insert_data.keys())):
            continue
        if "activo" in column_names and "activo" not in insert_data:
            insert_data["activo"] = True
        table = sa.table(
            table_name,
            *(sa.column(name) for name in insert_data.keys()),
        )
        lookup_columns = [key for key in insert_data.keys() if key in {"nombre", "slug", "valor"}]
        if lookup_columns:
            condition = " OR ".join(f"{col} = :{col}" for col in lookup_columns)
            params = {col: insert_data[col] for col in lookup_columns}
            existing = bind.execute(
                sa.text(f"SELECT 1 FROM {table_name} WHERE {condition} LIMIT 1"),
                params,
            ).first()
            if existing:
                continue
        op.bulk_insert(table, [insert_data])


def _remove_catalog_state() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    for table_name in inspector.get_table_names():
        if "estado" not in table_name or "equipo" not in table_name:
            continue
        columns = inspector.get_columns(table_name)
        column_names = {col["name"] for col in columns}
        if "nombre" in column_names:
            op.execute(sa.text(f"DELETE FROM {table_name} WHERE nombre = :nombre"), {"nombre": "En taller"})
        elif "valor" in column_names:
            op.execute(sa.text(f"DELETE FROM {table_name} WHERE valor = :valor"), {"valor": NEW_ESTADO})


def upgrade() -> None:
    op.add_column("equipos", sa.Column("observaciones", sa.Text(), nullable=True))
    _add_enum_value()
    _insert_catalog_state()


def downgrade() -> None:
    _remove_catalog_state()
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TYPE estado_equipo RENAME TO estado_equipo_old")
        sa.Enum(*ESTADO_VALUES, name="estado_equipo").create(bind)
        op.execute(
            """
            ALTER TABLE equipos
            ALTER COLUMN estado
            TYPE estado_equipo
            USING (
                CASE WHEN estado::text = :nuevo THEN :fallback ELSE estado::text END
            )::estado_equipo
            """,
            {"nuevo": NEW_ESTADO, "fallback": "servicio_tecnico"},
        )
        op.execute("DROP TYPE estado_equipo_old")
    op.drop_column("equipos", "observaciones")
