"""Helpers to build dashboard metrics payloads."""
from __future__ import annotations

from datetime import date, datetime, timedelta

from sqlalchemy import and_, func, or_, select
from sqlalchemy.sql import false

from app.extensions import db
from app.models import (
    EquipoInsumo,
    EstadoEquipo,
    EstadoLicencia,
    Equipo,
    Hospital,
    Insumo,
    Licencia,
    TipoEquipo,
    Usuario,
)
from app.utils.scope import ScopeValue, get_user_hospital_scope


def _to_title(value: str) -> str:
    return value.replace("_", " ").title()


def _apply_scope(query, column, scope: ScopeValue):
    if scope == "todos":
        return query
    if not scope:
        return query.filter(false())
    return query.filter(column.in_(scope))


def _insumo_scope_filter(scope: ScopeValue):
    if scope == "todos":
        return None
    if not scope:
        return false()
    associated = (
        select(1)
        .select_from(EquipoInsumo)
        .join(Equipo, EquipoInsumo.equipo_id == Equipo.id)
        .where(
            EquipoInsumo.insumo_id == Insumo.id,
            EquipoInsumo.fecha_desasociacion.is_(None),
            Equipo.hospital_id.in_(scope),
        )
        .exists()
    )
    any_association = (
        select(1)
        .select_from(EquipoInsumo)
        .where(
            EquipoInsumo.insumo_id == Insumo.id,
            EquipoInsumo.fecha_desasociacion.is_(None),
        )
        .exists()
    )
    return or_(associated, ~any_association)


def _apply_license_scope(query, scope: ScopeValue, *, joined: bool = False):
    if scope == "todos":
        return query
    if not scope:
        return query.filter(false())
    if not joined:
        query = query.join(Usuario, Usuario.id == Licencia.user_id)
    return query.filter(
        or_(
            Licencia.hospital_id.in_(scope),
            and_(
                Licencia.hospital_id.is_(None),
                Usuario.hospital_id.in_(scope),
            ),
        )
    )


def _build_scope_info(scope: ScopeValue) -> dict[str, object]:
    if scope == "todos":
        return {"type": "todos", "hospitales": [], "summary": "Todos los hospitales"}
    if not scope:
        return {"type": "limitado", "hospitales": [], "summary": "Sin hospitales asignados"}
    hospitales = (
        db.session.query(Hospital.id, Hospital.nombre)
        .filter(Hospital.id.in_(scope))
        .order_by(Hospital.nombre)
        .all()
    )
    data = [
        {"id": hospital_id, "nombre": nombre}
        for hospital_id, nombre in hospitales
    ]
    summary = ", ".join(item["nombre"] for item in data) if data else "Sin hospitales asignados"
    return {"type": "limitado", "hospitales": data, "summary": summary}


def _format_date(value: date | None) -> str:
    if not value:
        return "—"
    return value.strftime("%d/%m/%Y")


def collect_dashboard_metrics(user, top_supplies: int = 5) -> dict[str, object]:
    """Assemble counts and chart payloads for the dashboard respecting scope."""

    now = datetime.utcnow()
    since = now - timedelta(days=7)
    today = now.date()
    yesterday = today - timedelta(days=1)

    scope = get_user_hospital_scope(user)
    scope_info = _build_scope_info(scope)

    equipos_total_query = _apply_scope(db.session.query(func.count(Equipo.id)), Equipo.hospital_id, scope)
    equipos_total = equipos_total_query.scalar() or 0

    equipos_delta_query = _apply_scope(
        db.session.query(func.count(Equipo.id)).filter(Equipo.created_at >= since),
        Equipo.hospital_id,
        scope,
    )
    equipos_delta = equipos_delta_query.scalar() or 0

    insumo_filter = _insumo_scope_filter(scope)
    insumo_base = db.session.query(func.count(func.distinct(Insumo.id)))
    if insumo_filter is not None:
        insumo_base = insumo_base.filter(insumo_filter)
    insumos_total = insumo_base.scalar() or 0

    insumo_delta = db.session.query(func.count(func.distinct(Insumo.id))).filter(Insumo.created_at >= since)
    if insumo_filter is not None:
        insumo_delta = insumo_delta.filter(insumo_filter)
    insumos_delta_value = insumo_delta.scalar() or 0

    hospitales_query = db.session.query(func.count(Hospital.id))
    if scope != "todos":
        if not scope:
            hospitales_total = 0
        else:
            hospitales_total = hospitales_query.filter(Hospital.id.in_(scope)).scalar() or 0
    else:
        hospitales_total = hospitales_query.scalar() or 0

    hospitales_delta_query = db.session.query(func.count(Hospital.id)).filter(Hospital.created_at >= since)
    if scope != "todos":
        if not scope:
            hospitales_delta = 0
        else:
            hospitales_delta = hospitales_delta_query.filter(Hospital.id.in_(scope)).scalar() or 0
    else:
        hospitales_delta = hospitales_delta_query.scalar() or 0

    licencias_pendientes_query = db.session.query(func.count(Licencia.id)).filter(
        Licencia.estado == EstadoLicencia.SOLICITADA
    )
    licencias_pendientes_query = _apply_license_scope(licencias_pendientes_query, scope)
    licencias_pendientes = licencias_pendientes_query.scalar() or 0

    licencias_delta_query = db.session.query(func.count(Licencia.id)).filter(
        Licencia.estado == EstadoLicencia.SOLICITADA,
        Licencia.created_at >= since,
    )
    licencias_delta_query = _apply_license_scope(licencias_delta_query, scope)
    licencias_delta = licencias_delta_query.scalar() or 0

    # Licencias activas hoy
    licencias_hoy_query = db.session.query(
        Licencia.id,
        Licencia.tipo,
        Licencia.fecha_fin,
        Usuario.nombre,
        Usuario.apellido,
        Hospital.nombre,
    ).join(Usuario, Usuario.id == Licencia.user_id)
    licencias_hoy_query = licencias_hoy_query.outerjoin(Hospital, Hospital.id == Licencia.hospital_id)
    licencias_hoy_query = licencias_hoy_query.filter(
        Licencia.estado == EstadoLicencia.APROBADA,
        Licencia.fecha_inicio <= today,
        Licencia.fecha_fin >= today,
    )
    licencias_hoy_query = _apply_license_scope(licencias_hoy_query, scope, joined=True)
    licencias_hoy_rows = licencias_hoy_query.order_by(Usuario.nombre, Usuario.apellido).all()
    licencias_hoy = [
        {
            "id": licencia_id,
            "nombre": f"{nombre} {apellido}".strip(),
            "hospital": hospital_nombre or "Sin hospital",
            "hasta": _format_date(fecha_fin),
            "tipo": _to_title(tipo.value if hasattr(tipo, "value") else str(tipo)),
        }
        for licencia_id, tipo, fecha_fin, nombre, apellido, hospital_nombre in licencias_hoy_rows
    ]

    licencias_hoy_total = len(licencias_hoy)
    licencias_ayer_query = db.session.query(func.count(Licencia.id)).filter(
        Licencia.estado == EstadoLicencia.APROBADA,
        Licencia.fecha_inicio <= yesterday,
        Licencia.fecha_fin >= yesterday,
    )
    licencias_ayer_query = _apply_license_scope(licencias_ayer_query, scope)
    licencias_ayer_total = licencias_ayer_query.scalar() or 0

    licenses_today_payload = {
        "total": licencias_hoy_total,
        "delta": licencias_hoy_total - int(licencias_ayer_total),
        "items": licencias_hoy,
    }

    # Equipos por estado
    equipment_state_query = db.session.query(Equipo.estado, func.count(Equipo.id)).group_by(Equipo.estado)
    equipment_state_query = _apply_scope(equipment_state_query, Equipo.hospital_id, scope)
    equipment_state_rows = equipment_state_query.all()
    equipment_state = {
        "labels": [
            _to_title(row[0].value if isinstance(row[0], EstadoEquipo) else str(row[0]))
            for row in equipment_state_rows
        ],
        "values": [row[1] for row in equipment_state_rows],
    }

    # Equipos por tipo (top 7)
    equipment_type_total = func.count(Equipo.id).label("total")
    equipment_type_query = (
        db.session.query(TipoEquipo.nombre, equipment_type_total)
        .join(TipoEquipo, TipoEquipo.id == Equipo.tipo_id)
        .group_by(TipoEquipo.id, TipoEquipo.nombre)
    )
    equipment_type_query = _apply_scope(equipment_type_query, Equipo.hospital_id, scope)
    equipment_type_rows = (
        equipment_type_query.order_by(equipment_type_total.desc()).limit(7).all()
    )
    equipment_type = {
        "labels": [row[0] for row in equipment_type_rows],
        "values": [row[1] for row in equipment_type_rows],
    }

    # Stock de insumos por unidad/categoría
    insumo_stock_query = db.session.query(
        func.coalesce(Insumo.unidad_medida, "Sin unidad"),
        func.sum(Insumo.stock),
    )
    if insumo_filter is not None:
        insumo_stock_query = insumo_stock_query.filter(insumo_filter)
    insumo_stock_rows = (
        insumo_stock_query.group_by(Insumo.unidad_medida)
        .order_by(func.sum(Insumo.stock).desc())
        .limit(7)
        .all()
    )
    insumo_stock = {
        "labels": [row[0] or "Sin unidad" for row in insumo_stock_rows],
        "values": [int(row[1] or 0) for row in insumo_stock_rows],
    }

    critical_query = db.session.query(Insumo)
    if insumo_filter is not None:
        critical_query = critical_query.filter(insumo_filter)
    critical_rows: list[dict[str, object]] = []
    for insumo in critical_query.filter(
        Insumo.stock_minimo > 0,
        Insumo.stock <= Insumo.stock_minimo,
    ).all():
        stock_minimo = int(insumo.stock_minimo or 0)
        stock_actual = int(insumo.stock or 0)
        faltante = max(stock_minimo - stock_actual, 0)
        coverage = 0
        if stock_minimo > 0:
            coverage = max(min(round((stock_actual / stock_minimo) * 100), 100), 0)
        critical_rows.append(
            {
                "insumo": insumo,
                "faltante": faltante,
                "stock": stock_actual,
                "stock_minimo": stock_minimo,
                "coverage": coverage,
            }
        )

    critical_rows.sort(
        key=lambda item: (
            item["coverage"],
            -int(item["faltante"]),
            item["insumo"].nombre,
        )
    )
    critical_total = len(critical_rows)
    critical_supplies = [
        {
            "id": row["insumo"].id,
            "nombre": row["insumo"].nombre,
            "stock": row["stock"],
            "stock_minimo": row["stock_minimo"],
            "faltante": row["faltante"],
            "coverage_percent": int(row["coverage"]),
        }
        for row in critical_rows[:top_supplies]
    ]

    return {
        "generated_at": now.isoformat(),
        "generated_at_display": now.strftime("%d/%m/%Y %H:%M"),
        "kpis": [
            {
                "key": "equipos",
                "label": "Equipos",
                "value": int(equipos_total),
                "delta": int(equipos_delta),
            },
            {
                "key": "insumos",
                "label": "Insumos",
                "value": int(insumos_total),
                "delta": int(insumos_delta_value),
            },
            {
                "key": "hospitales",
                "label": "Instituciones",
                "value": int(hospitales_total),
                "delta": int(hospitales_delta),
            },
            {
                "key": "licencias_hoy",
                "label": "Licencias hoy",
                "value": int(licenses_today_payload["total"]),
                "delta": int(licenses_today_payload["delta"]),
            },
            {
                "key": "licencias_pendientes",
                "label": "Licencias pendientes",
                "value": int(licencias_pendientes),
                "delta": int(licencias_delta),
            },
        ],
        "charts": {
            "equipment_state": equipment_state,
            "equipment_type": equipment_type,
            "insumo_stock": insumo_stock,
        },
        "critical_supplies": critical_supplies,
        "critical_supplies_total": critical_total,
        "licenses_today": licenses_today_payload,
        "scope": scope_info,
    }

__all__ = ["collect_dashboard_metrics"]
