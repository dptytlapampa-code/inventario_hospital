from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .licencia import Base


class Hospital(Base):
    """Modelo de hospital."""

    __tablename__ = "hospitales"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)

    licencias = relationship("Licencia", back_populates="hospital")


__all__ = ["Hospital"]
