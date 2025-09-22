"""Business logic helpers for license workflow."""
from __future__ import annotations

from datetime import date, datetime

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
    comentario: str | None,
    requires_replacement: bool,
    reemplazo_id: int | None,
) -> Licencia:
    """Create and persist a new ``Licencia`` instance."""

    licencia = Licencia(
        usuario=usuario,
        hospital_id=hospital_id,
        tipo=tipo,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        motivo=motivo,
        comentario=comentario,
        requires_replacement=requires_replacement,
        reemplazo_id=reemplazo_id,
    )
    db.session.add(licencia)
    db.session.flush()
    return licencia


def licencias_superpuestas(usuario_id: int, inicio: date, fin: date, exclude_id: int | None = None) -> list[Licencia]:
    """Return approved licenses overlapping the given range."""

    query = (
        select(Licencia)
        .where(Licencia.usuario_id == usuario_id)
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
        .where(Licencia.usuario_id == usuario_id)
        .where(Licencia.estado == EstadoLicencia.APROBADA)
        .where(Licencia.fecha_inicio <= fecha)
        .where(Licencia.fecha_fin >= fecha)
    )
    return db.session.execute(query).first() is not None


def aprobar_licencia(licencia: Licencia, aprobador: Usuario, comentario: str | None = None) -> Licencia:
    """Approve ``licencia`` ensuring no overlaps."""

    if licencias_superpuestas(licencia.usuario_id, licencia.fecha_inicio, licencia.fecha_fin, licencia.id):
        raise ValueError("Ya existe una licencia aprobada que se superpone")
    licencia.aprobar(aprobador)
    if comentario:
        licencia.comentario = comentario
    db.session.commit()
    return licencia


def rechazar_licencia(licencia: Licencia, aprobador: Usuario, comentario: str | None = None) -> Licencia:
    licencia.rechazar(aprobador, comentario)
    db.session.commit()
    return licencia


def cancelar_licencia(licencia: Licencia, usuario: Usuario) -> Licencia:
    licencia.cancelar(usuario)
    db.session.commit()
    return licencia


def enviar_licencia(licencia: Licencia) -> Licencia:
    licencia.enviar_pendiente()
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
