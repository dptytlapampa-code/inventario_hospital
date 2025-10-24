"""Utilities to populate deterministic demo data for development environments."""
from __future__ import annotations

import logging
import os
from datetime import date, timedelta
from typing import Any, Iterable

from flask import current_app
from sqlalchemy import select
from sqlalchemy.orm import Session
from werkzeug.security import generate_password_hash

from app.models import (
    Acta,
    ActaItem,
    Adjunto,
    Auditoria,
    Docscan,
    Equipo,
    EstadoEquipo,
    Hospital,
    Insumo,
    InsumoMovimiento,
    Licencia,
    EstadoLicencia,
    Modulo,
    MovimientoTipo,
    Oficina,
    Permiso,
    Rol,
    Servicio,
    TipoActa,
    TipoAdjunto,
    TipoDocscan,
    TipoEquipo,
    TipoLicencia,
    Usuario,
)

LOGGER = logging.getLogger(__name__)
SUPERADMIN_USERNAME = "admin"
SUPERADMIN_PASSWORD = "123456"
SUPERADMIN_EMAIL = "admin@example.com"


def _is_verbose() -> bool:
    try:
        return bool(current_app.config.get("DEMO_SEED_VERBOSE"))
    except RuntimeError:  # pragma: no cover - executed when no app context
        return os.getenv("DEMO_SEED_VERBOSE", "0") in {"1", "true", "True"}


def _log(message: str, *, force_info: bool = False) -> None:
    if force_info:
        LOGGER.info(message)
        return
    if _is_verbose():
        LOGGER.info(message)


def ensure_superadmin(
    session: Session,
    *,
    username: str = SUPERADMIN_USERNAME,
    email: str = SUPERADMIN_EMAIL,
    password: str = SUPERADMIN_PASSWORD,
) -> Usuario:
    """Ensure the Superadmin role, permissions and default user exist."""

    role, role_created = _get_or_create(
        session,
        Rol,
        defaults={"descripcion": "Rol con todos los permisos"},
        nombre="Superadmin",
    )
    role.descripcion = "Rol con todos los permisos"
    _log(
        "Rol Superadmin %s."
        % ("creado" if role_created else "encontrado"),
        force_info=True,
    )
    session.flush()

    for modulo in Modulo:
        permiso, created_permiso = _get_or_create(
            session,
            Permiso,
            defaults={
                "rol": role,
                "can_read": True,
                "can_write": True,
                "allow_export": True,
            },
            rol_id=role.id,
            modulo=modulo,
            hospital_id=None,
        )
        updated = False
        if not permiso.can_read:
            permiso.can_read = True
            updated = True
        if not permiso.can_write:
            permiso.can_write = True
            updated = True
        if not permiso.allow_export:
            permiso.allow_export = True
            updated = True
        if created_permiso:
            _log(
                f"Permiso global para Superadmin sobre {modulo.value} creado.",
                force_info=True,
            )
        elif updated:
            _log(
                f"Permiso global para Superadmin sobre {modulo.value} actualizado.",
                force_info=True,
            )

    usuario_defaults = {
        "nombre": "Super Administrador",
        "dni": "20000000",
        "email": email,
        "rol": role,
        "activo": True,
        "password_hash": generate_password_hash(password),
    }
    usuario, user_created = _get_or_create(
        session,
        Usuario,
        defaults=usuario_defaults,
        username=username,
    )
    usuario.nombre = "Super Administrador"
    if not usuario.apellido:
        usuario.apellido = "Principal"
    usuario.email = email
    if not usuario.dni:
        usuario.dni = usuario_defaults["dni"]
    usuario.rol = role
    usuario.activo = True
    usuario.set_password(password)
    _log(
        "Usuario %s %s como Superadmin (password por defecto actualizada)."
        % (usuario.username, "creado" if user_created else "actualizado"),
        force_info=True,
    )
    return usuario


def promote_to_superadmin(
    session: Session, username: str, role: Rol | None = None
) -> Usuario | None:
    """Promote ``username`` to the Superadmin role if present."""

    if not username:
        return None

    target_role = role
    if target_role is None:
        target_role = ensure_superadmin(session).rol

    stmt = select(Usuario).filter_by(username=username)
    usuario = session.execute(stmt).scalar_one_or_none()
    if not usuario:
        LOGGER.warning(
            "Usuario %s no encontrado; no se puede promover a Superadmin.", username
        )
        return None

    if usuario.rol_id == target_role.id and usuario.activo:
        _log(
            f"Usuario {usuario.username} ya es Superadmin y está activo.",
            force_info=True,
        )
        return usuario

    usuario.rol = target_role
    usuario.activo = True
    _log(
        f"Usuario {usuario.username} promovido al rol Superadmin.",
        force_info=True,
    )
    return usuario


def _get_or_create(session: Session, model, defaults: dict[str, Any] | None = None, **filters: Any):
    stmt = select(model).filter_by(**filters)
    instance = session.execute(stmt).scalar_one_or_none()
    created = False
    if instance is None:
        params = dict(filters)
        if defaults:
            params.update(defaults)
        instance = model(**params)
        session.add(instance)
        session.flush()
        created = True
    elif defaults:
        for key, value in defaults.items():
            if value is not None:
                setattr(instance, key, value)
    return instance, created


def _ensure_roles(session: Session) -> dict[str, Rol]:
    roles: dict[str, Rol] = {}
    for nombre, descripcion in (
        ("Superadmin", "Acceso completo"),
        ("Admin", "Administración por hospital"),
        ("Tecnico", "Gestión operativa"),
        ("Lectura", "Solo consulta"),
    ):
        rol, created = _get_or_create(
            session,
            Rol,
            defaults={"descripcion": descripcion},
            nombre=nombre,
        )
        action = "creado" if created else "actualizado"
        _log(f"Rol {nombre} {action}.", force_info=True)
        roles[nombre.lower()] = rol
    return roles


def _ensure_hospital_structure(session: Session) -> tuple[list[Hospital], list[Servicio], list[Oficina]]:
    hospitales: list[Hospital] = []
    servicios: list[Servicio] = []
    oficinas: list[Oficina] = []

    hospital_specs = (
        {
            "nombre": "Hospital Dr. Lucio Molas",
            "codigo": "HLM",
            "localidad": "Santa Rosa",
            "direccion": "Av. Spinetto 1225, Santa Rosa",
            "zona_sanitaria": "I",
        },
        {
            "nombre": "Hospital René Favaloro",
            "codigo": "HRF",
            "localidad": "General Pico",
            "direccion": "Balcarce 222, General Pico",
            "zona_sanitaria": "II",
        },
        {
            "nombre": "Hospital José Curci",
            "codigo": "HJC",
            "localidad": "General Acha",
            "direccion": "Av. San Martín 350, General Acha",
            "zona_sanitaria": "III",
        },
    )

    for spec in hospital_specs:
        hospital, created = _get_or_create(
            session,
            Hospital,
            defaults={
                "codigo": spec["codigo"],
                "localidad": spec.get("localidad"),
                "direccion": spec["direccion"],
                "zona_sanitaria": spec.get("zona_sanitaria"),
                "provincia": "La Pampa",
                "tipo_institucion": "Hospital",
                "estado": "Activa",
            },
            nombre=spec["nombre"],
        )
        _log(f"Hospital {hospital.nombre} {'creado' if created else 'actualizado'}.")
        hospitales.append(hospital)

        servicio, created_serv = _get_or_create(
            session,
            Servicio,
            defaults={
                "descripcion": "Área responsable del parque informático",
                "hospital": hospital,
            },
            nombre="Soporte Informático",
            hospital_id=hospital.id,
        )
        _log(
            "Servicio Soporte Informático %s para %s."
            % ("creado" if created_serv else "actualizado", hospital.nombre)
        )
        servicios.append(servicio)

        oficina, created_off = _get_or_create(
            session,
            Oficina,
            defaults={
                "piso": "PB",
                "servicio": servicio,
                "hospital": hospital,
            },
            nombre="Deposito Central",
            servicio_id=servicio.id,
            hospital_id=hospital.id,
        )
        _log(
            "Oficina Deposito Central %s para %s."
            % ("creada" if created_off else "actualizada", hospital.nombre)
        )
        oficinas.append(oficina)

    return hospitales, servicios, oficinas


def _ensure_equipment_types(session: Session) -> dict[str, TipoEquipo]:
    tipos: dict[str, TipoEquipo] = {}
    for slug, nombre in (
        ("notebook", "Notebook"),
        ("impresora", "Impresora"),
        ("router", "Router"),
        ("switch", "Switch"),
        ("proyector", "Proyector"),
    ):
        tipo, created = _get_or_create(
            session,
            TipoEquipo,
            defaults={"nombre": nombre, "activo": True},
            slug=slug,
        )
        if created:
            tipo.nombre = nombre
            tipo.activo = True
        else:
            tipo.nombre = nombre
            tipo.activo = True
        _log(f"Tipo de equipo {nombre} {'creado' if created else 'sin cambios'}.")
        tipos[slug] = tipo
    return tipos


def _ensure_users(
    session: Session,
    roles: dict[str, Rol],
    hospitales: list[Hospital],
    servicios: list[Servicio],
    oficinas: list[Oficina],
) -> dict[str, Usuario]:
    usuarios: dict[str, Usuario] = {}
    user_specs = (
        {
            "username": SUPERADMIN_USERNAME,
            "nombre": "Super Administrador",
            "dni": "20000000",
            "email": SUPERADMIN_EMAIL,
            "rol": roles["superadmin"],
            "hospital": None,
            "servicio": None,
            "oficina": None,
            "password": SUPERADMIN_PASSWORD,
        },
        {
            "username": "admin_molas",
            "nombre": "Admin Molas",
            "dni": "20000001",
            "email": "admin.molas@salud.gob.ar",
            "rol": roles["admin"],
            "hospital": hospitales[0],
            "servicio": servicios[0],
            "oficina": oficinas[0],
            "password": "Cambiar123!",
        },
        {
            "username": "admin_favaloro",
            "nombre": "Admin Favaloro",
            "dni": "20000002",
            "email": "admin.favaloro@salud.gob.ar",
            "rol": roles["admin"],
            "hospital": hospitales[1],
            "servicio": servicios[1],
            "oficina": oficinas[1],
            "password": "Cambiar123!",
        },
        {
            "username": "tecnico_molas",
            "nombre": "Tecnico Molas",
            "dni": "20000003",
            "email": "tecnico.molas@salud.gob.ar",
            "rol": roles["tecnico"],
            "hospital": hospitales[0],
            "servicio": servicios[0],
            "oficina": oficinas[0],
            "password": "Cambiar123!",
        },
        {
            "username": "tecnico_favaloro",
            "nombre": "Tecnico Favaloro",
            "dni": "20000004",
            "email": "tecnico.favaloro@salud.gob.ar",
            "rol": roles["tecnico"],
            "hospital": hospitales[1],
            "servicio": servicios[1],
            "oficina": oficinas[1],
            "password": "Cambiar123!",
        },
        {
            "username": "consulta",
            "nombre": "Usuario Lectura",
            "dni": "20000005",
            "email": "lectura@salud.gob.ar",
            "rol": roles["lectura"],
            "hospital": hospitales[0],
            "servicio": servicios[0],
            "oficina": oficinas[0],
            "password": "Cambiar123!",
        },
    )

    for spec in user_specs:
        defaults = {
            "nombre": spec["nombre"],
            "dni": spec["dni"],
            "email": spec["email"],
            "rol": spec["rol"],
            "hospital": spec["hospital"],
            "servicio": spec["servicio"],
            "oficina": spec["oficina"],
            "activo": True,
            "password_hash": generate_password_hash(spec["password"]),
        }
        usuario, created = _get_or_create(
            session,
            Usuario,
            defaults=defaults,
            username=spec["username"],
        )
        usuario.nombre = spec["nombre"]
        usuario.dni = spec["dni"]
        usuario.email = spec["email"]
        usuario.rol = spec["rol"]
        usuario.hospital = spec["hospital"]
        usuario.servicio = spec["servicio"]
        usuario.oficina = spec["oficina"]
        usuario.activo = True
        usuario.set_password(spec["password"])
        action = "creado" if created else "actualizado"
        _log(f"Usuario {usuario.username} {action}.", force_info=True)
        usuarios[spec["username"]] = usuario

    return usuarios


def _ensure_permissions(
    session: Session, roles: dict[str, Rol], hospitales: Iterable[Hospital]
) -> None:
    for modulo in Modulo:
        permiso, created = _get_or_create(
            session,
            Permiso,
            defaults={
                "rol": roles["superadmin"],
                "can_read": True,
                "can_write": True,
                "allow_export": True,
            },
            rol_id=roles["superadmin"].id,
            modulo=modulo,
            hospital_id=None,
        )
        if created:
            permiso.rol = roles["superadmin"]
        permiso.can_read = True
        permiso.can_write = True
        permiso.allow_export = True
        _log(
            f"Permiso global para Superadmin sobre {modulo.value} garantizado.",
            force_info=True,
        )

    admin_modules = {
        Modulo.INVENTARIO,
        Modulo.INSUMOS,
        Modulo.ACTAS,
        Modulo.ADJUNTOS,
        Modulo.LICENCIAS,
        Modulo.DOCSCAN,
        Modulo.REPORTES,
    }

    for hospital in hospitales:
        for modulo in admin_modules:
            permiso, _ = _get_or_create(
                session,
                Permiso,
                defaults={
                    "rol": roles["admin"],
                    "hospital": hospital,
                    "can_read": True,
                    "can_write": True,
                    "allow_export": modulo == Modulo.REPORTES,
                },
                rol_id=roles["admin"].id,
                modulo=modulo,
                hospital_id=hospital.id,
            )
            permiso.can_read = True
            permiso.can_write = True
            permiso.allow_export = modulo == Modulo.REPORTES
        _log(
            f"Permisos de admin asegurados para {hospital.nombre}.",
            force_info=True,
        )

        tecnico_permisos = [
            (Modulo.INVENTARIO, True),
            (Modulo.ADJUNTOS, True),
            (Modulo.INSUMOS, False),
        ]
        for modulo, can_write in tecnico_permisos:
            permiso, _ = _get_or_create(
                session,
                Permiso,
                defaults={
                    "rol": roles["tecnico"],
                    "hospital": hospital,
                    "can_read": True,
                    "can_write": can_write,
                },
                rol_id=roles["tecnico"].id,
                modulo=modulo,
                hospital_id=hospital.id,
            )
            permiso.can_read = True
            permiso.can_write = can_write
            permiso.allow_export = False

        permiso, _ = _get_or_create(
            session,
            Permiso,
            defaults={
                "rol": roles["lectura"],
                "hospital": hospital,
                "can_read": True,
            },
            rol_id=roles["lectura"].id,
            modulo=Modulo.INVENTARIO,
            hospital_id=hospital.id,
        )
        permiso.can_read = True
        permiso.can_write = False
        permiso.allow_export = False
        _log(
            f"Permisos de lectura garantizados para {hospital.nombre}.",
            force_info=True,
        )


def _ensure_inventory(
    session: Session,
    tipos: dict[str, TipoEquipo],
    hospitales: list[Hospital],
    servicios: list[Servicio],
    oficinas: list[Oficina],
    usuarios: dict[str, Usuario],
) -> dict[str, Any]:
    equipos_context: dict[str, Equipo] = {}
    equipos_specs = (
        {
            "codigo": "EQ-0001",
            "tipo": tipos["notebook"],
            "estado": EstadoEquipo.OPERATIVO,
            "descripcion": "Notebook Lenovo ThinkPad",
            "marca": "Lenovo",
            "modelo": "T14",
            "numero_serie": "NB-0001",
            "hospital": hospitales[0],
            "servicio": servicios[0],
            "oficina": oficinas[0],
            "responsable": "Administración",
        },
        {
            "codigo": "EQ-0002",
            "tipo": tipos["impresora"],
            "estado": EstadoEquipo.SERVICIO_TECNICO,
            "descripcion": "Impresora HP LaserJet en revisión",
            "marca": "HP",
            "modelo": "M404",
            "numero_serie": "PR-0042",
            "hospital": hospitales[1],
            "servicio": servicios[1],
            "oficina": oficinas[1],
            "responsable": "Mesa de Entradas",
        },
        {
            "codigo": "EQ-0003",
            "tipo": tipos["router"],
            "estado": EstadoEquipo.OPERATIVO,
            "descripcion": "Router Cisco de enlace principal",
            "marca": "Cisco",
            "modelo": "RV340",
            "numero_serie": "RT-2048",
            "hospital": hospitales[0],
            "servicio": servicios[0],
            "oficina": oficinas[0],
            "responsable": "Infraestructura",
        },
    )

    for spec in equipos_specs:
        defaults = {
            "tipo": spec["tipo"],
            "estado": spec["estado"],
            "descripcion": spec["descripcion"],
            "marca": spec["marca"],
            "modelo": spec["modelo"],
            "numero_serie": spec["numero_serie"],
            "hospital": spec["hospital"],
            "servicio": spec["servicio"],
            "oficina": spec["oficina"],
            "responsable": spec["responsable"],
        }
        equipo, created = _get_or_create(
            session,
            Equipo,
            defaults=defaults,
            codigo=spec["codigo"],
        )
        for key, value in defaults.items():
            setattr(equipo, key, value)
        equipos_context[spec["codigo"]] = equipo
        if created and not equipo.historial:
            equipo.registrar_evento(
                usuarios.get("admin_molas"),
                "Alta",
                "Carga inicial de inventario",
            )
            _log(f"Historial inicial agregado para el equipo {equipo.codigo}.")

    insumos_context: dict[str, Insumo] = {}
    insumo_specs = (
        {
            "nombre": "Tóner 85A",
            "numero_serie": "TN-85A",
            "descripcion": "Tóner negro para impresoras HP",
            "unidad_medida": "unidad",
            "stock": 10,
            "stock_minimo": 3,
            "costo_unitario": 85.50,
        },
        {
            "nombre": "Cable de red CAT6",
            "numero_serie": "CB-100",
            "descripcion": "Cable UTP de 3 metros",
            "unidad_medida": "unidad",
            "stock": 30,
            "stock_minimo": 10,
            "costo_unitario": 6.75,
        },
        {
            "nombre": "Batería UPS",
            "numero_serie": "UPS-BAT-01",
            "descripcion": "Batería de recambio para UPS",
            "unidad_medida": "unidad",
            "stock": 6,
            "stock_minimo": 2,
            "costo_unitario": 145.00,
        },
    )

    for spec in insumo_specs:
        insumo, _ = _get_or_create(
            session,
            Insumo,
            defaults={
                "numero_serie": spec["numero_serie"],
                "descripcion": spec["descripcion"],
                "unidad_medida": spec["unidad_medida"],
            },
            nombre=spec["nombre"],
        )
        insumo.numero_serie = spec["numero_serie"]
        insumo.descripcion = spec["descripcion"]
        insumo.unidad_medida = spec["unidad_medida"]
        insumo.stock = spec["stock"]
        insumo.stock_minimo = spec["stock_minimo"]
        insumo.costo_unitario = spec["costo_unitario"]
        insumos_context[spec["nombre"]] = insumo

    # Vincular insumos a equipos para mostrar relaciones.
    equipo_insumo_map = {
        "EQ-0001": ["Cable de red CAT6"],
        "EQ-0002": ["Tóner 85A"],
    }
    for equipo_codigo, insumo_names in equipo_insumo_map.items():
        equipo = equipos_context[equipo_codigo]
        for nombre in insumo_names:
            insumo = insumos_context[nombre]
            if insumo not in equipo.insumos:
                equipo.insumos.append(insumo)

    # Registrar un movimiento de stock demostrativo.
    insumo = insumos_context["Tóner 85A"]
    stmt = select(InsumoMovimiento).filter_by(
        insumo_id=insumo.id,
        motivo="Entrega a servicio técnico",
        tipo=MovimientoTipo.EGRESO,
    )
    movimiento_existente = session.execute(stmt).scalar_one_or_none()
    if movimiento_existente is None:
        movimiento = InsumoMovimiento(
            insumo=insumo,
            usuario=usuarios.get("tecnico_favaloro"),
            tipo=MovimientoTipo.EGRESO,
            cantidad=2,
            motivo="Entrega a servicio técnico",
            observaciones="Se dejó constancia en acta de servicio.",
        )
        session.add(movimiento)
        _log("Movimiento de insumo registrado para Tóner 85A.")

    return {"equipos": equipos_context, "insumos": insumos_context}


def _ensure_licenses(
    session: Session,
    usuarios: dict[str, Usuario],
    hospitales: list[Hospital],
) -> None:
    licencia_specs = (
        {
            "usuario": usuarios["tecnico_molas"],
            "hospital": hospitales[0],
            "tipo": TipoLicencia.VACACIONES,
            "estado": EstadoLicencia.APROBADA,
            "fecha_inicio": date.today() - timedelta(days=5),
            "fecha_fin": date.today() + timedelta(days=5),
            "motivo": "Vacaciones programadas",
        },
        {
            "usuario": usuarios["tecnico_favaloro"],
            "hospital": hospitales[1],
            "tipo": TipoLicencia.ENFERMEDAD,
            "estado": EstadoLicencia.SOLICITADA,
            "fecha_inicio": date.today() + timedelta(days=7),
            "fecha_fin": date.today() + timedelta(days=12),
            "motivo": "Licencia médica",
        },
    )

    for spec in licencia_specs:
        licencia, _ = _get_or_create(
            session,
            Licencia,
            defaults={
                "usuario": spec["usuario"],
                "hospital": spec["hospital"],
                "tipo": spec["tipo"],
                "motivo": spec["motivo"],
                "fecha_inicio": spec["fecha_inicio"],
                "fecha_fin": spec["fecha_fin"],
                "estado": spec["estado"],
            },
            user_id=spec["usuario"].id,
            motivo=spec["motivo"],
        )
        licencia.hospital = spec["hospital"]
        licencia.tipo = spec["tipo"]
        licencia.estado = spec["estado"]
        licencia.fecha_inicio = spec["fecha_inicio"]
        licencia.fecha_fin = spec["fecha_fin"]


def _ensure_supporting_records(
    session: Session,
    hospitales: list[Hospital],
    usuarios: dict[str, Usuario],
    inventory: dict[str, Any],
) -> None:
    equipos = inventory["equipos"]
    superadmin_usuario = usuarios[SUPERADMIN_USERNAME]

    acta, _ = _get_or_create(
        session,
        Acta,
        defaults={
            "tipo": TipoActa.ENTREGA,
            "hospital": hospitales[0],
            "usuario": usuarios["admin_molas"],
            "observaciones": "Entrega inicial de equipamiento para el área administrativa.",
            "pdf_path": "uploads/actas/acta_demo.pdf",
        },
        numero="ACT-0001",
    )
    acta.tipo = TipoActa.ENTREGA
    acta.hospital = hospitales[0]
    acta.usuario = usuarios["admin_molas"]
    acta.observaciones = "Entrega inicial de equipamiento para el área administrativa."
    acta.pdf_path = "uploads/actas/acta_demo.pdf"

    stmt = select(ActaItem).filter_by(acta_id=acta.id, equipo_id=equipos["EQ-0001"].id)
    if session.execute(stmt).scalar_one_or_none() is None:
        item = ActaItem(
            acta=acta,
            equipo=equipos["EQ-0001"],
            cantidad=1,
            descripcion="Notebook asignada al sector administrativo",
        )
        session.add(item)
        _log("Item de acta agregado para EQ-0001.")

    adjunto_stmt = select(Adjunto).filter_by(
        equipo_id=equipos["EQ-0001"].id,
        filename="factura_notebook.pdf",
    )
    if session.execute(adjunto_stmt).scalar_one_or_none() is None:
        adjunto = Adjunto(
            equipo=equipos["EQ-0001"],
            filename="factura_notebook.pdf",
            path="uploads/adjuntos/factura_notebook.pdf",
            tipo=TipoAdjunto.FACTURA,
            descripcion="Factura de compra",
            uploaded_by=usuarios["admin_molas"],
        )
        session.add(adjunto)
        _log("Adjunto demo creado para EQ-0001.")

    docscan_stmt = select(Docscan).filter_by(filename="nota_pedido.pdf")
    if session.execute(docscan_stmt).scalar_one_or_none() is None:
        documento = Docscan(
            titulo="Nota de pedido",
            tipo=TipoDocscan.NOTA,
            filename="nota_pedido.pdf",
            path="uploads/docscan/nota_pedido.pdf",
            comentario="Solicitud firmada por dirección",
            usuario=superadmin_usuario,
            hospital=hospitales[0],
        )
        session.add(documento)
        _log("Documento escaneado demo creado.")

    auditoria_stmt = select(Auditoria).filter_by(
        accion="seed",
        modulo="setup",
        descripcion="Carga inicial de datos",
    )
    if session.execute(auditoria_stmt).scalar_one_or_none() is None:
        auditoria = Auditoria(
            usuario=superadmin_usuario,
            hospital=hospitales[0],
            modulo="setup",
            accion="seed",
            descripcion="Carga inicial de datos",
        )
        session.add(auditoria)
        _log("Entrada de auditoría demo registrada.")


def load_demo_data(sqlalchemy_db) -> None:
    """Populate demo catalogues and sample data in an idempotent way."""

    session: Session = sqlalchemy_db.session
    superadmin_user = ensure_superadmin(session)
    roles = _ensure_roles(session)
    roles["superadmin"] = superadmin_user.rol
    hospitales, servicios, oficinas = _ensure_hospital_structure(session)
    tipos = _ensure_equipment_types(session)
    usuarios = _ensure_users(session, roles, hospitales, servicios, oficinas)
    _ensure_permissions(session, roles, hospitales)
    inventory = _ensure_inventory(session, tipos, hospitales, servicios, oficinas, usuarios)
    _ensure_licenses(session, usuarios, hospitales)
    _ensure_supporting_records(session, hospitales, usuarios, inventory)
    _log(
        "Seed demo listo. Usuario inicial: %s / %s" % (SUPERADMIN_USERNAME, SUPERADMIN_PASSWORD)
    )


__all__ = ["ensure_superadmin", "promote_to_superadmin", "load_demo_data"]

