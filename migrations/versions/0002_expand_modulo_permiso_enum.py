"""Expand modulo_permiso enum with new values used by the application."""
from __future__ import annotations

from collections.abc import Iterable

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002_expand_modulo_permiso_enum"
down_revision = "0001_initial"
branch_labels = None
depends_on = None

ENUM_NAME = "modulo_permiso"
# Values requested explicitly (upper-case)
UPPERCASE_VALUES: tuple[str, ...] = (
    "INVENTARIO",
    "INSUMOS",
    "EQUIPOS",
    "DOCSCAN",
    "PERMISOS",
    "LICENCIAS",
    "USUARIOS",
    "VLANS",
)
# Lower-case variants that are either already present or used by the application
LOWERCASE_VALUES: tuple[str, ...] = tuple(value.lower() for value in UPPERCASE_VALUES)

ORIGINAL_VALUES: tuple[str, ...] = (
    "inventario",
    "insumos",
    "actas",
    "adjuntos",
    "docscan",
    "reportes",
    "auditoria",
    "licencias",
)

def _enum_labels(bind) -> set[str]:
    query = sa.text(
        """
        SELECT e.enumlabel
        FROM pg_type t
        JOIN pg_enum e ON t.oid = e.enumtypid
        WHERE t.typname = :name
        """
    )
    result = bind.execute(query, {"name": ENUM_NAME})
    return {row[0] for row in result}


def _add_enum_values(values: Iterable[str]) -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    existing = _enum_labels(bind)
    missing = [value for value in values if value not in existing]
    for value in missing:
        with op.get_context().autocommit_block():
            op.execute(
                sa.text(f'ALTER TYPE "{ENUM_NAME}" ADD VALUE :value').bindparams(value=value)
            )


def upgrade() -> None:
    # Ensure both upper and lower-case values exist for compatibility
    _add_enum_values((*UPPERCASE_VALUES, *LOWERCASE_VALUES))


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    disallowed_query = sa.text(
        """
        SELECT DISTINCT modulo::text
        FROM permisos
        WHERE modulo::text <> ALL(:allowed)
        """
    )
    allowed = list(ORIGINAL_VALUES)
    disallowed = {
        row[0]
        for row in bind.execute(
            disallowed_query.bindparams(sa.bindparam("allowed", allowed, type_=sa.ARRAY(sa.Text())))
        )
    }
    if disallowed:
        raise RuntimeError(
            "No se puede revertir la migración mientras existan valores de modulo_permiso "
            f"no soportados por el esquema original: {', '.join(sorted(disallowed))}"
        )

    temp_enum = f"{ENUM_NAME}_old"
    with op.get_context().autocommit_block():
        op.execute(sa.text(f'ALTER TYPE "{ENUM_NAME}" RENAME TO "{temp_enum}"'))

    original_enum = postgresql.ENUM(*ORIGINAL_VALUES, name=ENUM_NAME)
    original_enum.create(bind, checkfirst=False)

    op.execute(
        sa.text(
            f'ALTER TABLE permisos ALTER COLUMN modulo TYPE "{ENUM_NAME}" '
            f'USING modulo::text::"{ENUM_NAME}"'
        )
    )

    with op.get_context().autocommit_block():
        op.execute(sa.text(f'DROP TYPE "{temp_enum}"'))
