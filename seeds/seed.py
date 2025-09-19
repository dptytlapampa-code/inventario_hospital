"""Seed script that loads a small but coherent dataset."""


from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from config import Config
from app.models.hospital import Hospital
from app.models.rol import Rol
from app.models.usuario import Usuario
from app.models.permisos import Permiso, Modulo
from app.models.licencia import Licencia, TipoLicencia, EstadoLicencia
from app.models.equipo import Equipo, TipoEquipo, EstadoEquipo
from app.models.insumo import Insumo
from app.models.acta import Acta, TipoActa, ActaItem
from app.models.adjunto import Adjunto, TipoAdjunto
from app.models.docscan import Docscan, TipoDocscan
from app.models.auditoria import Auditoria


def _get_or_create(session: Session, model, /, *, defaults: dict | None = None, **filters):
    """Return an instance matching ``filters`` or create it with ``defaults``."""

    stmt = select(model).filter_by(**filters)
    instance = session.scalars(stmt).first()
    if instance:
        return instance
    params = {**filters, **(defaults or {})}
    instance = model(**params)  # type: ignore[arg-type]
    session.add(instance)
    session.flush([instance])
    return instance


def run() -> None:
    """Populate the database with hospitals, roles, users and demo data."""

    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI, future=True)

    with Session(engine) as session:
        hospitals = {
            name: _get_or_create(session, Hospital, nombre=name)
            for name in (
                "Hospital Dr. Lucio Molas",
                "Hospital René Favaloro",
            )
        }

        roles = {
            name: _get_or_create(session, Rol, nombre=name)
            for name in ("Superadmin", "Admin", "Tecnico")
        }

        users = {}
        for data in (
            {
                "key": "superadmin",
                "nombre": "Administrador General",
                "email": "admin@hospital.test",
                "rol": roles["Superadmin"],
            },
            {
                "key": "admin_lucio",
                "nombre": "Admin Lucio Molas",
                "email": "admin.lucio@hospital.test",
                "rol": roles["Admin"],
            },
            {
                "key": "admin_rene",
                "nombre": "Admin René Favaloro",
                "email": "admin.rene@hospital.test",
                "rol": roles["Admin"],
            },
            {
                "key": "tecnico_lucio",
                "nombre": "Técnico Lucio Molas",
                "email": "tecnico.lucio@hospital.test",
                "rol": roles["Tecnico"],
            },
            {
                "key": "tecnico_rene",
                "nombre": "Técnico René Favaloro",
                "email": "tecnico.rene@hospital.test",
                "rol": roles["Tecnico"],
            },
        ):
            usuario = _get_or_create(
                session,
                Usuario,
                email=data["email"],
                defaults={"nombre": data["nombre"], "rol": data["rol"]},
            )
            if usuario.rol is None:
                usuario.rol = data["rol"]
            users[data["key"]] = usuario

        # Assign granular permissions per role and hospital.
        full_modules = list(Modulo)
        for modulo in full_modules:
            _get_or_create(
                session,
                Permiso,
                rol_id=roles["Superadmin"].id,
                modulo=modulo,
                hospital_id=None,
                defaults={"can_read": True, "can_write": True},
            )

        admin_modules_write = {
            Modulo.INVENTARIO,
            Modulo.INSUMOS,
            Modulo.ACTAS,
            Modulo.ADJUNTOS,
            Modulo.DOCSCAN,
            Modulo.LICENCIAS,
        }
        for hospital in hospitals.values():
            for modulo in full_modules:
                _get_or_create(
                    session,
                    Permiso,
                    rol_id=roles["Admin"].id,
                    hospital_id=hospital.id,
                    modulo=modulo,
                    defaults={
                        "can_read": True,
                        "can_write": modulo in admin_modules_write,
                    },
                )
                _get_or_create(
                    session,
                    Permiso,
                    rol_id=roles["Tecnico"].id,
                    hospital_id=hospital.id,
                    modulo=modulo,
                    defaults={"can_read": True, "can_write": False},
                )

        # Sample licences for each technician.
        for key, hospital_name in (
            ("tecnico_lucio", "Hospital Dr. Lucio Molas"),
            ("tecnico_rene", "Hospital René Favaloro"),
        ):
            technician = users[key]
            hospital = hospitals[hospital_name]
            stmt = select(Licencia).filter_by(usuario_id=technician.id, hospital_id=hospital.id)
            licencia = session.scalars(stmt).first()
            if not licencia:
                licencia = Licencia(
                    usuario=technician,
                    hospital=hospital,
                    tipo=TipoLicencia.TEMPORAL,
                    estado=EstadoLicencia.APROBADA,
                    requires_replacement=False,
                )
                session.add(licencia)

        # Inventory examples.
        notebook = _get_or_create(
            session,
            Equipo,
            numero_serie="NB-LM-001",
            defaults={
                "tipo": TipoEquipo.NOTEBOOK,
                "estado": EstadoEquipo.OPERATIVO,
                "descripcion": "Notebook HP ProBook",
                "hospital": hospitals["Hospital Dr. Lucio Molas"],
            },
        )
        router = _get_or_create(
            session,
            Equipo,
            numero_serie="RT-RF-001",
            defaults={
                "tipo": TipoEquipo.ROUTER,
                "estado": EstadoEquipo.OPERATIVO,
                "descripcion": "Router Cisco para sector administrativo",
                "hospital": hospitals["Hospital René Favaloro"],
            },
        )

        toner = _get_or_create(
            session,
            Insumo,
            nombre="Tóner HP 17A",
            defaults={"numero_serie": "TN-17A-2024", "stock": 10},
        )
        cable = _get_or_create(
            session,
            Insumo,
            nombre="Cable UTP categoría 6",
            defaults={"numero_serie": None, "stock": 50},
        )

        if toner not in notebook.insumos:
            notebook.insumos.append(toner)
        if cable not in router.insumos:
            router.insumos.append(cable)

        # Example acta and related entries.
        acta = _get_or_create(
            session,
            Acta,
            tipo=TipoActa.ENTREGA,
            usuario_id=users["admin_lucio"].id,
            hospital_id=hospitals["Hospital Dr. Lucio Molas"].id,
        )
        _get_or_create(
            session,
            ActaItem,
            acta_id=acta.id,
            equipo_id=notebook.id,
            defaults={"descripcion": "Entrega de notebook para guardia"},
        )

        _get_or_create(
            session,
            Adjunto,
            filename="acta_entrega_notebook.pdf",
            equipo_id=notebook.id,
            defaults={
                "tipo": TipoAdjunto.ACTA,
            },
        )

        _get_or_create(
            session,
            Docscan,
            filename="nota_reparacion_router.pdf",
            usuario_id=users["admin_rene"].id,
            defaults={
                "tipo": TipoDocscan.NOTA,
            },
        )

        _get_or_create(
            session,
            Auditoria,
            accion="seed_data",
            tabla="system",
            registro_id=0,
            defaults={"usuario": users["superadmin"]},
        )

        session.commit()
        print("Datos de ejemplo cargados correctamente.")


if __name__ == "__main__":
    run()
