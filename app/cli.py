"""Custom Flask CLI commands for local development utilities."""
from __future__ import annotations

import click
from datetime import datetime

from flask.cli import with_appcontext

from app import db
from app.models import Hospital, Oficina, Rol, Servicio, Usuario


@click.command("seed-demo")
@with_appcontext
def seed_demo() -> None:
    """Populate the database with a minimal demo dataset."""

    rol = Rol.query.filter_by(nombre="Superadmin").first()
    if not rol:
        rol = Rol(
            nombre="Superadmin",
            descripcion="Rol con todos los permisos",
            created_at=datetime.utcnow(),
        )
        db.session.add(rol)
        db.session.flush()

    hosp = Hospital.query.first()
    if not hosp:
        hosp = Hospital(nombre="Hospital Demo")
        db.session.add(hosp)
        db.session.flush()

    u = Usuario.query.filter_by(username="admin").first()
    if not u:
        u = Usuario(
            username="admin",
            nombre="Admin",
            dni="00000000",
            apellido="Demo",
            email="admin@example.com",
            activo=True,
            rol_id=rol.id,
            hospital_id=hosp.id,
        )
        u.set_password("123456")
        db.session.add(u)

    db.session.commit()
    print("OK: seed de demo cargado. Usuario admin / 123456")


# Referencias silenciosas para evitar advertencias de importaciones no utilizadas
# cuando herramientas estáticas analizan el módulo.
_ = (Servicio, Oficina)
