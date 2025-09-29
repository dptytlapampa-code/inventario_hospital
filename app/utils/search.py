"""Helpers for building adaptive text search queries."""
from __future__ import annotations

from typing import Iterable, Sequence

from sqlalchemy import ColumnElement, func, literal, or_, select
from sqlalchemy.orm import Query

from app.extensions import db


def _is_postgres() -> bool:
    bind = db.session.get_bind()  # type: ignore[arg-type]
    if not bind:
        return False
    return bind.dialect.name == "postgresql"


def _coalesce_concat(columns: Sequence[ColumnElement[str]]) -> ColumnElement[str]:
    values: list[ColumnElement[str]] = [func.coalesce(col, literal("")) for col in columns]
    return func.concat_ws(literal(" "), *values)


def build_text_search(columns: Sequence[ColumnElement[str]], term: str) -> ColumnElement[bool]:
    """Return a SQL expression that matches ``term`` across ``columns``."""

    sanitized = (term or "").strip()
    if not sanitized:
        raise ValueError("term must be a non-empty string")

    if _is_postgres() and len(sanitized) >= 3:
        vector = func.to_tsvector("spanish", _coalesce_concat(columns))
        query = func.plainto_tsquery("spanish", sanitized)
        return vector.op("@@")(query)

    like = f"%{sanitized}%"
    return or_(*[col.ilike(like) for col in columns])


def apply_text_search(query: Query, columns: Sequence[ColumnElement[str]], term: str) -> Query:
    """Apply a flexible text search filter to ``query``."""

    sanitized = (term or "").strip()
    if not sanitized:
        return query
    try:
        condition = build_text_search(columns, sanitized)
    except ValueError:
        return query
    return query.filter(condition)


def paginate_query(query: Query, *, page: int, per_page: int):
    """Paginate ``query`` enforcing sane defaults."""

    page = max(page, 1)
    per_page = max(1, min(per_page, 100))
    return query.paginate(page=page, per_page=per_page, error_out=False)


def search_lookup(model, columns: Sequence[ColumnElement[str]], term: str, limit: int = 10):
    """Return a list of model instances matching ``term`` limited to ``limit``."""

    query = select(model)
    sanitized = (term or "").strip()
    if sanitized:
        query = query.filter(build_text_search(columns, sanitized))
    query = query.order_by(columns[0]).limit(limit)
    return db.session.execute(query).scalars().all()


__all__ = [
    "apply_text_search",
    "build_text_search",
    "paginate_query",
    "search_lookup",
]
