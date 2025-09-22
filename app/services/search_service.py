"""Helper functions to perform global search across models."""
from __future__ import annotations

from sqlalchemy import or_, select

from app.extensions import db
from app.models import Docscan, Equipo, Insumo, Licencia, Usuario


def global_search(query: str) -> list[dict[str, str]]:
    """Search across key models returning unified dictionaries."""

    if not query:
        return []
    like = f"%{query.lower()}%"

    resultados: list[dict[str, str]] = []

    equipos = db.session.execute(
        select(Equipo).where(
            or_(
                Equipo.descripcion.ilike(like),
                Equipo.codigo.ilike(like),
                Equipo.numero_serie.ilike(like),
            )
        )
    ).scalars()
    for equipo in equipos:
        resultados.append(
            {
                "tipo": "Equipo",
                "titulo": equipo.descripcion or equipo.codigo or "Equipo",
                "detalle": equipo.numero_serie or "",
                "url": f"/equipos/{equipo.id}",
            }
        )

    insumos = db.session.execute(
        select(Insumo).where(
            or_(Insumo.nombre.ilike(like), Insumo.numero_serie.ilike(like))
        )
    ).scalars()
    for insumo in insumos:
        resultados.append(
            {
                "tipo": "Insumo",
                "titulo": insumo.nombre,
                "detalle": f"Stock: {insumo.stock}",
                "url": f"/insumos/{insumo.id}",
            }
        )

    usuarios = db.session.execute(
        select(Usuario).where(
            or_(Usuario.nombre.ilike(like), Usuario.email.ilike(like), Usuario.username.ilike(like))
        )
    ).scalars()
    for usuario in usuarios:
        resultados.append(
            {
                "tipo": "Usuario",
                "titulo": usuario.nombre,
                "detalle": usuario.email,
                "url": "#",
            }
        )

    docscan = db.session.execute(
        select(Docscan).where(or_(Docscan.titulo.ilike(like), Docscan.comentario.ilike(like)))
    ).scalars()
    for doc in docscan:
        resultados.append(
            {
                "tipo": "Documento",
                "titulo": doc.titulo,
                "detalle": doc.tipo.value,
                "url": f"/docscan/{doc.id}",
            }
        )

    licencias = db.session.execute(
        select(Licencia).where(Licencia.motivo.ilike(like))
    ).scalars()
    for lic in licencias:
        resultados.append(
            {
                "tipo": "Licencia",
                "titulo": lic.usuario.nombre,
                "detalle": f"{lic.fecha_inicio:%d/%m/%Y} - {lic.fecha_fin:%d/%m/%Y}",
                "url": f"/licencias/{lic.id}/detalle",
            }
        )

    return resultados


__all__ = ["global_search"]
