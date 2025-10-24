"""Servicios para la generación de reportes exportables."""

from __future__ import annotations

import re
import unicodedata
from datetime import datetime, timezone
from decimal import Decimal
from io import BytesIO

from sqlalchemy.orm import selectinload

from app.extensions import db
from app.models import (
    Equipo,
    EquipoInsumo,
    Hospital,
    HospitalUsuarioRol,
    Insumo,
    Usuario,
    Vlan,
    VlanDispositivo,
)
from app.utils.xlsx import SimpleXLSX


def _format_date(value) -> str:
    return value.strftime("%Y-%m-%d") if value else ""


def _format_decimal(value: Decimal | float | int | None) -> str:
    if value is None:
        return ""
    return f"{value:.2f}"


def _slugify(value: str | None) -> str:
    base = (value or "").strip()
    if not base:
        return "todos"
    normalized = unicodedata.normalize("NFKD", base).encode("ascii", "ignore").decode("ascii")
    cleaned = re.sub(r"[^a-z0-9]+", "-", normalized.lower()).strip("-")
    return cleaned or "todos"


def generar_reporte_excel(hospital_id: int | None = None) -> tuple[BytesIO, str]:
    """Construye un archivo Excel con los datos relevantes del sistema."""

    hospitales_query = db.session.query(Hospital).order_by(Hospital.nombre.asc())
    if hospital_id:
        hospitales_query = hospitales_query.filter(Hospital.id == hospital_id)
    hospitales = hospitales_query.all()
    hospitales_ids = {hospital.id for hospital in hospitales}

    libro = SimpleXLSX()

    libro.add_sheet(
        "Hospitales",
        [
            ["ID", "Nombre", "Código", "Localidad", "Dirección", "Teléfono", "Nivel"],
            *[
                [
                    hospital.id,
                    hospital.nombre,
                    hospital.codigo or "",
                    hospital.localidad or "",
                    hospital.direccion or "",
                    hospital.telefono or "",
                    hospital.nivel_complejidad or "",
                ]
                for hospital in hospitales
            ],
        ],
    )

    equipos_query = (
        db.session.query(Equipo)
        .options(
            selectinload(Equipo.hospital),
            selectinload(Equipo.tipo),
            selectinload(Equipo.servicio),
            selectinload(Equipo.oficina),
        )
        .order_by(Equipo.hospital_id.asc(), Equipo.codigo.asc())
    )
    if hospitales_ids:
        equipos_query = equipos_query.filter(Equipo.hospital_id.in_(hospitales_ids))
    equipos = equipos_query.all()
    libro.add_sheet(
        "Equipos",
        [
            [
                "Hospital",
                "Código",
                "Tipo",
                "Estado",
                "Marca",
                "Modelo",
                "Número de serie",
                "Servicio",
                "Oficina",
                "Responsable",
                "Fecha ingreso",
                "Fecha instalación",
                "Garantía hasta",
            ],
            *[
                [
                    equipo.hospital.nombre if equipo.hospital else "",
                    equipo.codigo or "",
                    equipo.tipo.nombre if equipo.tipo else "",
                    equipo.estado.value if equipo.estado else "",
                    equipo.marca or "",
                    equipo.modelo or "",
                    equipo.numero_serie or "",
                    equipo.servicio.nombre if equipo.servicio else "",
                    equipo.oficina.nombre if equipo.oficina else "",
                    equipo.responsable or "",
                    _format_date(equipo.fecha_ingreso),
                    _format_date(equipo.fecha_instalacion),
                    _format_date(equipo.garantia_hasta),
                ]
                for equipo in equipos
            ],
        ],
    )

    insumos_query = (
        db.session.query(Insumo)
        .options(
            selectinload(Insumo.asignaciones)
            .selectinload(EquipoInsumo.equipo)
            .selectinload(Equipo.hospital)
        )
        .order_by(Insumo.nombre.asc())
    )
    insumos = insumos_query.all()
    filas_insumos: list[list[object]] = []
    for insumo in insumos:
        hospitales_relacionados: dict[int, str] = {}
        for asignacion in insumo.asignaciones:
            equipo = getattr(asignacion, "equipo", None)
            if equipo and equipo.hospital:
                hospitales_relacionados[equipo.hospital.id] = equipo.hospital.nombre
        if hospitales_ids:
            filtrados = {
                hid: nombre
                for hid, nombre in hospitales_relacionados.items()
                if hid in hospitales_ids
            }
            if not filtrados:
                continue
            nombres_hospital = sorted(set(filtrados.values()))
        else:
            nombres_hospital = sorted(set(hospitales_relacionados.values()))
        filas_insumos.append(
            [
                ", ".join(nombres_hospital),
                insumo.nombre,
                insumo.numero_serie or "",
                insumo.unidad_medida or "",
                insumo.stock,
                insumo.stock_minimo,
                _format_decimal(insumo.costo_unitario),
            ]
        )
    libro.add_sheet(
        "Insumos",
        [
            [
                "Hospitales asociados",
                "Nombre",
                "Número de serie",
                "Unidad",
                "Stock",
                "Stock mínimo",
                "Costo unitario",
            ],
            *filas_insumos,
        ],
    )

    usuarios_query = (
        db.session.query(Usuario)
        .options(
            selectinload(Usuario.rol),
            selectinload(Usuario.hospital),
            selectinload(Usuario.hospitales_roles).selectinload(HospitalUsuarioRol.hospital),
        )
        .order_by(Usuario.apellido.asc(), Usuario.nombre.asc())
    )
    usuarios = usuarios_query.all()
    filas_usuarios: list[list[object]] = []
    for usuario in usuarios:
        hospitales_usuario = []
        if usuario.hospital:
            hospitales_usuario.append(usuario.hospital)
        for relacion in usuario.hospitales_roles:
            if relacion.hospital and relacion.hospital not in hospitales_usuario:
                hospitales_usuario.append(relacion.hospital)
        if hospitales_ids:
            hospitales_usuario = [
                hospital
                for hospital in hospitales_usuario
                if hospital.id in hospitales_ids
            ]
            if not hospitales_usuario:
                continue
        filas_usuarios.append(
            [
                ", ".join(sorted({hospital.nombre for hospital in hospitales_usuario})),
                usuario.username,
                f"{usuario.apellido or ''}, {usuario.nombre}".strip(", "),
                usuario.dni,
                usuario.email,
                usuario.telefono or "",
                usuario.rol.nombre if usuario.rol else "",
                "Sí" if usuario.activo else "No",
            ]
        )
    libro.add_sheet(
        "Usuarios",
        [
            [
                "Hospitales",
                "Usuario",
                "Nombre completo",
                "DNI",
                "Email",
                "Teléfono",
                "Rol",
                "Activo",
            ],
            *filas_usuarios,
        ],
    )

    vlans_query = (
        db.session.query(Vlan)
        .options(
            selectinload(Vlan.hospital),
            selectinload(Vlan.servicio),
            selectinload(Vlan.oficina),
        )
        .order_by(Vlan.hospital_id.asc(), Vlan.identificador.asc())
    )
    if hospitales_ids:
        vlans_query = vlans_query.filter(Vlan.hospital_id.in_(hospitales_ids))
    vlans = vlans_query.all()
    libro.add_sheet(
        "VLANs",
        [
            [
                "Hospital",
                "Nombre",
                "Identificador",
                "Descripción",
                "Servicio",
                "Oficina",
            ],
            *[
                [
                    vlan.hospital.nombre if vlan.hospital else "",
                    vlan.nombre,
                    vlan.identificador,
                    vlan.descripcion or "",
                    vlan.servicio.nombre if vlan.servicio else "",
                    vlan.oficina.nombre if vlan.oficina else "",
                ]
                for vlan in vlans
            ],
        ],
    )

    dispositivos_query = (
        db.session.query(VlanDispositivo)
        .options(
            selectinload(VlanDispositivo.vlan),
            selectinload(VlanDispositivo.hospital),
            selectinload(VlanDispositivo.servicio),
            selectinload(VlanDispositivo.oficina),
        )
        .order_by(VlanDispositivo.hospital_id.asc(), VlanDispositivo.direccion_ip.asc())
    )
    if hospitales_ids:
        dispositivos_query = dispositivos_query.filter(
            VlanDispositivo.hospital_id.in_(hospitales_ids)
        )
    dispositivos = dispositivos_query.all()
    libro.add_sheet(
        "VLAN Dispositivos",
        [
            [
                "Hospital",
                "VLAN",
                "Equipo",
                "Host",
                "Dirección IP",
                "Dirección MAC",
                "Servicio",
                "Oficina",
            ],
            *[
                [
                    dispositivo.hospital.nombre if dispositivo.hospital else "",
                    dispositivo.vlan.identificador if dispositivo.vlan else "",
                    dispositivo.nombre_equipo,
                    dispositivo.host or "",
                    dispositivo.direccion_ip,
                    dispositivo.direccion_mac or "",
                    dispositivo.servicio.nombre if dispositivo.servicio else "",
                    dispositivo.oficina.nombre if dispositivo.oficina else "",
                ]
                for dispositivo in dispositivos
            ],
        ],
    )

    stream = libro.to_bytes()
    timestamp = datetime.now(timezone.utc)
    if hospital_id and hospitales:
        nombre_archivo = (
            f"inventario_{_slugify(hospitales[0].nombre)}_{timestamp:%Y%m%d_%H%M%S}.xlsx"
        )
    else:
        nombre_archivo = f"inventario_todos_{timestamp:%Y%m%d_%H%M%S}.xlsx"
    return stream, nombre_archivo


__all__ = ["generar_reporte_excel"]
