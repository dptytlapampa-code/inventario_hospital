"""Business logic helpers for license workflow."""
from __future__ import annotations

from datetime import date

from sqlalchemy import select

from app.extensions import db
from app.models import EstadoLicencia, Licencia, Usuario


def crear_licencia(
    *,
    usuario: Usuario,
    hospital_id: int | None,
    tipo,
    fecha_inicio: date,
    fecha_fin: date,
    motivo: str,
) -> Licencia:
    """Create and persist a new ``Licencia`` instance."""

    licencia = Licencia(
        usuario=usuario,
        hospital_id=hospital_id,
        tipo=tipo,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        motivo=motivo,
    )
    db.session.add(licencia)
    db.session.flush()
    return licencia


def licencias_superpuestas(usuario_id: int, inicio: date, fin: date, exclude_id: int | None = None) -> list[Licencia]:
    """Return approved licenses overlapping the given range."""

    query = (
        select(Licencia)
        .where(Licencia.user_id == usuario_id)
        .where(Licencia.estado == EstadoLicencia.APROBADA)
        .where(Licencia.fecha_inicio <= fin)
        .where(Licencia.fecha_fin >= inicio)
    )
    if exclude_id:
        query = query.where(Licencia.id != exclude_id)
    return list(db.session.scalars(query))


def usuario_con_licencia_activa(usuario_id: int, fecha: date | None = None) -> bool:
    """Return ``True`` if the user has an approved license covering ``fecha``."""

    fecha = fecha or date.today()
    query = (
        select(Licencia)
        .where(Licencia.user_id == usuario_id)
        .where(Licencia.estado == EstadoLicencia.APROBADA)
        .where(Licencia.fecha_inicio <= fecha)
        .where(Licencia.fecha_fin >= fecha)
    )
    return db.session.execute(query).first() is not None


def aprobar_licencia(licencia: Licencia, aprobador: Usuario) -> Licencia:
    """Approve ``licencia`` ensuring no overlaps."""

    if licencias_superpuestas(licencia.user_id, licencia.fecha_inicio, licencia.fecha_fin, licencia.id):
        raise ValueError("Ya existe una licencia aprobada que se superpone")
    licencia.aprobar(aprobador)
    db.session.commit()
    return licencia


def rechazar_licencia(
    licencia: Licencia, aprobador: Usuario, motivo: str | None = None
) -> Licencia:
    licencia.rechazar(aprobador, motivo)
    db.session.commit()
    return licencia


def cancelar_licencia(licencia: Licencia, usuario: Usuario) -> Licencia:
    licencia.cancelar(usuario)
    db.session.commit()
    return licencia


def enviar_licencia(licencia: Licencia) -> Licencia:
    if licencia.estado != EstadoLicencia.SOLICITADA:
        raise ValueError("La licencia ya fue procesada")
    db.session.commit()
    return licencia


__all__ = [
    "crear_licencia",
    "licencias_superpuestas",
    "usuario_con_licencia_activa",
    "aprobar_licencia",
    "rechazar_licencia",
    "cancelar_licencia",
    "enviar_licencia",
]
