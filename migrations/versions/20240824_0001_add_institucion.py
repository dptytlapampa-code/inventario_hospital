"""Add institucion model and migrate hospital relations."""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20240824_0001_add_institucion"
down_revision = "0006_hospital_localidad_complejidad"
branch_labels = None
depends_on = None


def _drop_unique_constraint_if_exists(table: str, columns: set[str]) -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if table not in inspector.get_table_names():
        return
    for constraint in inspector.get_unique_constraints(table):
        if set(constraint.get("column_names", [])) == columns:
            op.drop_constraint(constraint["name"], table_name=table, type_="unique")
            break


def _drop_fk_on_column(table: str, column: str) -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if table not in inspector.get_table_names():
        return
    for fk in inspector.get_foreign_keys(table):
        if column in fk.get("constrained_columns", []):
            op.drop_constraint(fk["name"], table_name=table, type_="foreignkey")


def _drop_index_if_exists(table: str, index_name: str) -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if table not in inspector.get_table_names():
        return
    for index in inspector.get_indexes(table):
        if index.get("name") == index_name:
            op.drop_index(index_name, table_name=table)
            break


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "hospitales" in inspector.get_table_names():
        _drop_unique_constraint_if_exists("hospitales", {"nombre"})
        _drop_unique_constraint_if_exists("hospitales", {"codigo"})
        op.rename_table("hospitales", "instituciones")
        inspector = sa.inspect(bind)

    if "instituciones" in inspector.get_table_names():
        columns = {column["name"] for column in inspector.get_columns("instituciones")}
        if "localidad" in columns:
            op.execute(
                sa.text(
                    "UPDATE instituciones SET localidad = 'Sin localidad' WHERE localidad IS NULL"
                )
            )
        with op.batch_alter_table("instituciones") as batch_op:
            if "nombre" in columns:
                batch_op.alter_column(
                    "nombre",
                    existing_type=sa.String(length=200),
                    type_=sa.String(length=255),
                    existing_nullable=False,
                )
            if "codigo" in columns:
                batch_op.alter_column(
                    "codigo",
                    existing_type=sa.String(length=20),
                    type_=sa.String(length=50),
                    existing_nullable=True,
                )
            if "localidad" in columns:
                batch_op.alter_column(
                    "localidad",
                    existing_type=sa.String(length=120),
                    nullable=False,
                )
            if "telefono" in columns:
                batch_op.drop_column("telefono")
            if "nivel_complejidad" in columns:
                batch_op.drop_column("nivel_complejidad")
            batch_op.add_column(sa.Column("tipo_institucion", sa.String(length=50), nullable=True))
            batch_op.add_column(sa.Column("provincia", sa.String(length=120), nullable=True))
            batch_op.add_column(sa.Column("zona_sanitaria", sa.String(length=120), nullable=True))
            batch_op.add_column(sa.Column("estado", sa.String(length=50), nullable=True))
            batch_op.alter_column(
                "created_at",
                server_default=sa.text("now()"),
                existing_type=sa.DateTime(timezone=True),
                existing_nullable=False,
            )
            batch_op.alter_column(
                "updated_at",
                server_default=sa.text("now()"),
                existing_type=sa.DateTime(timezone=True),
                existing_nullable=False,
            )
        op.execute(
            sa.text(
                "UPDATE instituciones SET tipo_institucion = 'Hospital' WHERE tipo_institucion IS NULL"
            )
        )
        op.execute(
            sa.text(
                "UPDATE instituciones SET provincia = COALESCE(provincia, 'La Pampa')"
            )
        )
        op.execute(
            sa.text("UPDATE instituciones SET estado = COALESCE(estado, 'Activa')")
        )
        with op.batch_alter_table("instituciones") as batch_op:
            batch_op.alter_column(
                "tipo_institucion",
                existing_type=sa.String(length=50),
                nullable=False,
                server_default=sa.text("'Hospital'"),
            )
            batch_op.alter_column(
                "provincia",
                existing_type=sa.String(length=120),
                nullable=False,
                server_default=sa.text("'La Pampa'"),
            )
            batch_op.alter_column(
                "estado",
                existing_type=sa.String(length=50),
                nullable=False,
                server_default=sa.text("'Activa'"),
            )
        _drop_index_if_exists("instituciones", "ix_hospitales_codigo")
        op.create_index(
            "ix_instituciones_codigo", "instituciones", ["codigo"], unique=False
        )
        op.create_unique_constraint(
            "uq_institucion_nombre_localidad",
            "instituciones",
            ["nombre", "localidad"],
        )

    inspector = sa.inspect(bind)
    if "servicios" in inspector.get_table_names():
        _drop_unique_constraint_if_exists("servicios", {"hospital_id", "nombre"})
        _drop_fk_on_column("servicios", "hospital_id")
        with op.batch_alter_table("servicios") as batch_op:
            batch_op.add_column(sa.Column("institucion_id", sa.Integer(), nullable=True))
            batch_op.create_foreign_key(
                "fk_servicios_institucion_id_instituciones",
                "instituciones",
                ["institucion_id"],
                ["id"],
                ondelete="CASCADE",
            )
        op.execute(sa.text("UPDATE servicios SET institucion_id = hospital_id"))
        with op.batch_alter_table("servicios") as batch_op:
            batch_op.alter_column(
                "institucion_id", existing_type=sa.Integer(), nullable=False
            )
            batch_op.drop_column("hospital_id")
        op.create_unique_constraint(
            "uq_servicio_nombre_institucion",
            "servicios",
            ["institucion_id", "nombre"],
        )

    inspector = sa.inspect(bind)
    if "oficinas" in inspector.get_table_names():
        _drop_fk_on_column("oficinas", "hospital_id")
        with op.batch_alter_table("oficinas") as batch_op:
            batch_op.add_column(sa.Column("institucion_id", sa.Integer(), nullable=True))
            batch_op.create_foreign_key(
                "fk_oficinas_institucion_id_instituciones",
                "instituciones",
                ["institucion_id"],
                ["id"],
                ondelete="CASCADE",
            )
        op.execute(sa.text("UPDATE oficinas SET institucion_id = hospital_id"))
        with op.batch_alter_table("oficinas") as batch_op:
            batch_op.alter_column(
                "institucion_id", existing_type=sa.Integer(), nullable=False
            )
            batch_op.drop_column("hospital_id")


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "oficinas" in inspector.get_table_names():
        with op.batch_alter_table("oficinas") as batch_op:
            batch_op.add_column(sa.Column("hospital_id", sa.Integer(), nullable=True))
        op.execute(sa.text("UPDATE oficinas SET hospital_id = institucion_id"))
        _drop_fk_on_column("oficinas", "institucion_id")
        with op.batch_alter_table("oficinas") as batch_op:
            batch_op.create_foreign_key(
                "fk_oficinas_hospital_id_hospitales",
                "hospitales",
                ["hospital_id"],
                ["id"],
                ondelete="CASCADE",
            )
            batch_op.alter_column("hospital_id", existing_type=sa.Integer(), nullable=False)
            batch_op.drop_column("institucion_id")

    inspector = sa.inspect(bind)
    if "servicios" in inspector.get_table_names():
        _drop_unique_constraint_if_exists("servicios", {"institucion_id", "nombre"})
        with op.batch_alter_table("servicios") as batch_op:
            batch_op.add_column(sa.Column("hospital_id", sa.Integer(), nullable=True))
        op.execute(sa.text("UPDATE servicios SET hospital_id = institucion_id"))
        _drop_fk_on_column("servicios", "institucion_id")
        with op.batch_alter_table("servicios") as batch_op:
            batch_op.create_foreign_key(
                "fk_servicios_hospital_id_hospitales",
                "hospitales",
                ["hospital_id"],
                ["id"],
                ondelete="CASCADE",
            )
            batch_op.alter_column("hospital_id", existing_type=sa.Integer(), nullable=False)
            batch_op.drop_column("institucion_id")
        op.create_unique_constraint(
            "uq_servicio_nombre_hospital",
            "servicios",
            ["hospital_id", "nombre"],
        )

    inspector = sa.inspect(bind)
    if "instituciones" in inspector.get_table_names():
        _drop_unique_constraint_if_exists("instituciones", {"nombre", "localidad"})
        op.drop_index("ix_instituciones_codigo", table_name="instituciones")
        with op.batch_alter_table("instituciones") as batch_op:
            batch_op.alter_column(
                "estado",
                existing_type=sa.String(length=50),
                server_default=None,
                nullable=True,
            )
            batch_op.alter_column(
                "provincia",
                existing_type=sa.String(length=120),
                server_default=None,
                nullable=True,
            )
            batch_op.alter_column(
                "tipo_institucion",
                existing_type=sa.String(length=50),
                server_default=None,
                nullable=True,
            )
            batch_op.alter_column(
                "localidad",
                existing_type=sa.String(length=120),
                nullable=True,
            )
            batch_op.alter_column(
                "codigo",
                existing_type=sa.String(length=50),
                type_=sa.String(length=20),
                existing_nullable=True,
            )
            batch_op.alter_column(
                "nombre",
                existing_type=sa.String(length=255),
                type_=sa.String(length=200),
                existing_nullable=False,
            )
            batch_op.alter_column(
                "created_at",
                server_default=sa.text("CURRENT_TIMESTAMP"),
                existing_type=sa.DateTime(timezone=True),
                existing_nullable=False,
            )
            batch_op.alter_column(
                "updated_at",
                server_default=sa.text("CURRENT_TIMESTAMP"),
                existing_type=sa.DateTime(timezone=True),
                existing_nullable=False,
            )
            batch_op.drop_column("estado")
            batch_op.drop_column("zona_sanitaria")
            batch_op.drop_column("provincia")
            batch_op.drop_column("tipo_institucion")
            batch_op.add_column(sa.Column("telefono", sa.String(length=50), nullable=True))
            batch_op.add_column(sa.Column("nivel_complejidad", sa.Integer(), nullable=True))
        op.rename_table("instituciones", "hospitales")
        op.create_index("ix_hospitales_codigo", "hospitales", ["codigo"], unique=False)
        op.create_unique_constraint("uq_hospital_nombre", "hospitales", ["nombre"])
        op.create_unique_constraint("uq_hospital_codigo", "hospitales", ["codigo"])

    # Esquema revertido al estado previo a la migración de instituciones.
