"""Create tables to manage VLANs and associated devices."""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0005_vlans"
down_revision = "0004_equipos_observaciones_en_taller"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "vlans",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(length=120), nullable=False),
        sa.Column("identificador", sa.String(length=50), nullable=False),
        sa.Column("descripcion", sa.String(length=255), nullable=True),
        sa.Column("hospital_id", sa.Integer(), nullable=False),
        sa.Column("servicio_id", sa.Integer(), nullable=True),
        sa.Column("oficina_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            server_onupdate=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["hospital_id"], ["hospitales.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["servicio_id"], ["servicios.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["oficina_id"], ["oficinas.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("hospital_id", "identificador", name="uq_vlan_hospital_identificador"),
    )

    op.create_table(
        "vlan_dispositivos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("vlan_id", sa.Integer(), nullable=False),
        sa.Column("nombre_equipo", sa.String(length=150), nullable=False),
        sa.Column("host", sa.String(length=120), nullable=True),
        sa.Column("direccion_ip", sa.String(length=45), nullable=False),
        sa.Column("direccion_mac", sa.String(length=32), nullable=True),
        sa.Column("hospital_id", sa.Integer(), nullable=False),
        sa.Column("servicio_id", sa.Integer(), nullable=True),
        sa.Column("oficina_id", sa.Integer(), nullable=True),
        sa.Column("notas", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            server_onupdate=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["vlan_id"], ["vlans.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["hospital_id"], ["hospitales.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["servicio_id"], ["servicios.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["oficina_id"], ["oficinas.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("direccion_ip", name="uq_vlan_dispositivo_ip"),
    )


def downgrade() -> None:
    op.drop_table("vlan_dispositivos")
    op.drop_table("vlans")
