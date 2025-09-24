"""Helpers to build dashboard metrics payloads."""
from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import func

from app.extensions import db
from app.models import (
    EstadoEquipo,
    EstadoLicencia,
    Equipo,
    Hospital,
    Insumo,
    Licencia,
    TipoEquipo,
)


def _to_title(value: str) -> str:
    return value.replace("_", " ").title()


def collect_dashboard_metrics() -> dict[str, object]:
    """Assemble counts and chart payloads for the dashboard."""

    now = datetime.utcnow()
    since = now - timedelta(days=7)

    equipos_total = db.session.query(func.count(Equipo.id)).scalar() or 0
    equipos_delta = (
        db.session.query(func.count(Equipo.id))
        .filter(Equipo.created_at >= since)
        .scalar()
        or 0
    )

    insumos_total = db.session.query(func.count(Insumo.id)).scalar() or 0
    insumos_delta = (
        db.session.query(func.count(Insumo.id))
        .filter(Insumo.created_at >= since)
        .scalar()
        or 0
    )

    hospitales_total = db.session.query(func.count(Hospital.id)).scalar() or 0
    hospitales_delta = (
        db.session.query(func.count(Hospital.id))
        .filter(Hospital.created_at >= since)
        .scalar()
        or 0
    )

    licencias_pendientes = (
        db.session.query(func.count(Licencia.id))
        .filter(Licencia.estado == EstadoLicencia.PENDIENTE)
        .scalar()
        or 0
    )
    licencias_delta = (
        db.session.query(func.count(Licencia.id))
        .filter(
            Licencia.estado == EstadoLicencia.PENDIENTE,
            Licencia.created_at >= since,
        )
        .scalar()
        or 0
    )

    # Equipos por estado
    equipment_state_rows = (
        db.session.query(Equipo.estado, func.count(Equipo.id))
        .group_by(Equipo.estado)
        .all()
    )
    equipment_state = {
        "labels": [_to_title(row[0].value if isinstance(row[0], EstadoEquipo) else str(row[0])) for row in equipment_state_rows],
        "values": [row[1] for row in equipment_state_rows],
    }

    # Equipos por tipo (top 7)
    equipment_type_rows = (
        db.session.query(Equipo.tipo, func.count(Equipo.id).label("total"))
        .group_by(Equipo.tipo)
        .order_by(func.count(Equipo.id).desc())
        .limit(7)
        .all()
    )
    equipment_type = {
        "labels": [_to_title(row[0].value if isinstance(row[0], TipoEquipo) else str(row[0])) for row in equipment_type_rows],
        "values": [row[1] for row in equipment_type_rows],
    }

    # Stock de insumos por unidad/categoría
    insumo_stock_rows = (
        db.session.query(
            func.coalesce(Insumo.unidad_medida, "Sin unidad"),
            func.sum(Insumo.stock),
        )
        .group_by(Insumo.unidad_medida)
        .order_by(func.sum(Insumo.stock).desc())
        .limit(7)
        .all()
    )
    insumo_stock = {
        "labels": [row[0] or "Sin unidad" for row in insumo_stock_rows],
        "values": [int(row[1] or 0) for row in insumo_stock_rows],
    }

    faltante = (Insumo.stock_minimo - Insumo.stock).label("faltante")
    critical_query = (
        db.session.query(Insumo, faltante)
        .filter(Insumo.stock_minimo > 0, Insumo.stock <= Insumo.stock_minimo)
        .order_by(faltante.desc(), Insumo.nombre)
        .limit(8)
    )
    critical_supplies = [
        {
            "id": insumo.id,
            "nombre": insumo.nombre,
            "stock": int(insumo.stock or 0),
            "stock_minimo": int(insumo.stock_minimo or 0),
            "faltante": int(max(falta, 0)),
        }
        for insumo, falta in critical_query
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
                "delta": int(insumos_delta),
            },
            {
                "key": "hospitales",
                "label": "Hospitales",
                "value": int(hospitales_total),
                "delta": int(hospitales_delta),
            },
            {
                "key": "licencias",
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
    }


__all__ = ["collect_dashboard_metrics"]
