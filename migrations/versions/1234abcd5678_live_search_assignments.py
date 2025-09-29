"""Search helpers, hospital assignments and audit improvements."""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = "1234abcd5678"
down_revision = "2f1a4b2b1234"
branch_labels = None
depends_on = None


def _is_postgres(connection) -> bool:
    return connection.dialect.name == "postgresql"


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    # Enable extensions for advanced text search on PostgreSQL.
    if _is_postgres(bind):
        bind.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
        bind.execute("CREATE EXTENSION IF NOT EXISTS unaccent")

    # Create association table for usuario/hospital assignments.
    op.create_table(
        "hospital_usuario_rol",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id"), nullable=False),
        sa.Column("hospital_id", sa.Integer(), sa.ForeignKey("hospitales.id"), nullable=False),
        sa.Column("rol_id", sa.Integer(), sa.ForeignKey("roles.id"), nullable=False),
        sa.UniqueConstraint("usuario_id", "hospital_id", name="uq_usuario_hospital_asignacion"),
    )

    if "auditoria" in inspector.get_table_names():
        op.rename_table("auditoria", "auditorias")
        inspector = inspect(bind)

    columns = {col["name"]: col for col in inspector.get_columns("auditorias")}

    if "tabla" in columns:
        op.drop_column("auditorias", "tabla")
    if "registro_id" in columns:
        op.drop_column("auditorias", "registro_id")
    if "datos" in columns:
        op.drop_column("auditorias", "datos")
    if "fecha" in columns:
        op.alter_column("auditorias", "fecha", new_column_name="created_at")

    if "hospital_id" not in columns:
        op.add_column("auditorias", sa.Column("hospital_id", sa.Integer(), sa.ForeignKey("hospitales.id")))
    if "entidad" not in columns:
        op.add_column("auditorias", sa.Column("entidad", sa.String(length=50)))
    if "entidad_id" not in columns:
        op.add_column("auditorias", sa.Column("entidad_id", sa.Integer()))
    if "descripcion" not in columns:
        op.add_column("auditorias", sa.Column("descripcion", sa.Text()))
    if "cambios" not in columns:
        op.add_column("auditorias", sa.Column("cambios", sa.JSON()))

    op.create_index("ix_auditorias_usuario", "auditorias", ["usuario_id"])
    op.create_index("ix_auditorias_hospital", "auditorias", ["hospital_id"])
    op.create_index("ix_auditorias_modulo", "auditorias", ["modulo"])
    op.create_index("ix_auditorias_accion", "auditorias", ["accion"])
    op.create_index("ix_auditorias_created_at", "auditorias", ["created_at"])

    if _is_postgres(bind):
        op.execute(
            """
            CREATE INDEX IF NOT EXISTS ix_usuarios_search ON usuarios
            USING gin (to_tsvector('spanish', coalesce(nombre,'') || ' ' || coalesce(apellido,'') || ' ' || coalesce(username,'') || ' ' || coalesce(email,'')));
            """
        )
        op.execute(
            """
            CREATE INDEX IF NOT EXISTS ix_hospitales_search ON hospitales
            USING gin (to_tsvector('spanish', coalesce(nombre,'') || ' ' || coalesce(direccion,'') || ' ' || coalesce(codigo,'')));
            """
        )


def downgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        op.execute("DROP INDEX IF EXISTS ix_hospitales_search")
        op.execute("DROP INDEX IF EXISTS ix_usuarios_search")

    op.drop_index("ix_auditorias_created_at", table_name="auditorias")
    op.drop_index("ix_auditorias_accion", table_name="auditorias")
    op.drop_index("ix_auditorias_modulo", table_name="auditorias")
    op.drop_index("ix_auditorias_hospital", table_name="auditorias")
    op.drop_index("ix_auditorias_usuario", table_name="auditorias")

    op.drop_column("auditorias", "cambios")
    op.drop_column("auditorias", "descripcion")
    op.drop_column("auditorias", "entidad_id")
    op.drop_column("auditorias", "entidad")
    op.drop_column("auditorias", "hospital_id")

    op.alter_column("auditorias", "created_at", new_column_name="fecha")
    op.add_column("auditorias", sa.Column("datos", sa.Text()))
    op.add_column("auditorias", sa.Column("registro_id", sa.Integer()))
    op.add_column("auditorias", sa.Column("tabla", sa.String(length=100)))

    op.rename_table("auditorias", "auditoria")

    op.drop_table("hospital_usuario_rol")
