"""Importa instituciones desde un CSV externo."""
from __future__ import annotations

import argparse
import csv
import logging
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from tqdm import tqdm

from app import create_app
from app.extensions import db
from app.models import Institucion, Oficina, Servicio

LOGGER = logging.getLogger("seed_instituciones")

SMALL_WORDS = {"de", "del", "la", "las", "los", "y", "e", "al"}
DEFAULT_SERVICES: dict[str, list[str]] = {
    "Administración": ["Admisión", "Jefatura", "Dirección", "Oficina 1"],
    "Consultorios": ["Consultorio 1", "Consultorio 2"],
    "Guardia": ["Enfermería"],
}


class TqdmLoggingHandler(logging.Handler):
    """Handler que integra logging con tqdm para evitar solapamientos."""

    def emit(self, record: logging.LogRecord) -> None:  # pragma: no cover - manejador simple
        try:
            msg = self.format(record)
            tqdm.write(msg)
        except Exception:  # pragma: no cover - defensivo
            print(record.getMessage())


@dataclass
class SeedStats:
    created: int = 0
    updated: int = 0
    skipped: int = 0
    services_created: int = 0
    offices_created: int = 0


def configure_logging(verbose: bool = False) -> None:
    LOGGER.setLevel(logging.DEBUG if verbose else logging.INFO)
    handler = TqdmLoggingHandler()
    handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
    LOGGER.handlers.clear()
    LOGGER.addHandler(handler)


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = [dict(row) for row in reader]
    return rows


def normalize_text(value: str) -> str:
    cleaned = value.strip()
    cleaned = re.sub(r"[\"'`]+", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip(" -")


def strip_prefixes(value: str) -> str:
    patterns = [
        r"^ESTAB\.?\s*ASISTENCIAL\s*",
        r"^ESTABLECIMIENTO\s+ASISTENCIAL\s*",
        r"^HOSP\.?\s*",
        r"^HOSPITAL\s+",
    ]
    result = value
    for pattern in patterns:
        result = re.sub(pattern, "", result, flags=re.IGNORECASE).strip()
    return result


def smart_title(value: str) -> str:
    if not value:
        return value
    tokens = re.split(r"(\s+|-)", value.lower())
    formatted: list[str] = []
    for token in tokens:
        if not token:
            continue
        if token.isspace() or token == "-":
            formatted.append(token)
            continue
        if token in SMALL_WORDS and formatted:
            formatted.append(token)
            continue
        if token.endswith(".") and len(token) <= 4:
            formatted.append(token.capitalize())
            continue
        formatted.append(token.capitalize())
    result = "".join(formatted)
    return result.replace(" De La ", " de la ").replace(" De Los ", " de los ")


def normalize_institucion_name(raw_name: str, localidad: str) -> tuple[str, str]:
    cleaned_name = smart_title(strip_prefixes(normalize_text(raw_name)))
    localidad_title = smart_title(normalize_text(localidad))
    final_name = f"Hospital {cleaned_name} - {localidad_title}" if cleaned_name else f"Hospital - {localidad_title}"
    return final_name, localidad_title


def get_field(row: dict[str, str], candidates: Iterable[str]) -> str | None:
    for candidate in candidates:
        if candidate in row and row[candidate] not in (None, ""):
            return str(row[candidate]).strip()
    return None


def ensure_defaults(institucion: Institucion, stats: SeedStats) -> None:
    for service_name, office_names in DEFAULT_SERVICES.items():
        servicio = (
            Servicio.query.filter_by(institucion_id=institucion.id, nombre=service_name).one_or_none()
        )
        if not servicio:
            servicio = Servicio(nombre=service_name, institucion=institucion)
            db.session.add(servicio)
            db.session.flush()
            stats.services_created += 1
        for office_name in office_names:
            oficina = (
                Oficina.query.filter_by(
                    institucion_id=institucion.id, servicio_id=servicio.id, nombre=office_name
                ).one_or_none()
            )
            if not oficina:
                oficina = Oficina(
                    nombre=office_name,
                    servicio=servicio,
                    institucion=institucion,
                )
                db.session.add(oficina)
                stats.offices_created += 1


def process_rows(rows: list[dict[str, str]]) -> SeedStats:
    stats = SeedStats()
    progress = tqdm(rows, desc="Instituciones", unit="inst.")
    for index, row in enumerate(progress, start=2):
        codigo = get_field(row, ["Cód.", "Cod.", "Codigo", "Código"])
        nombre_raw = get_field(row, ["Institución", "Institucion", "Nombre"])
        localidad_raw = get_field(row, ["Localidad"])
        zona_sanitaria = get_field(row, ["Zona Sanitaria", "Zona", "Zona sanitaria"])

        if not nombre_raw or not localidad_raw:
            stats.skipped += 1
            LOGGER.warning(
                "Fila %s omitida: faltan campos obligatorios (Institución o Localidad).",
                index,
            )
            continue

        display_name, localidad = normalize_institucion_name(nombre_raw, localidad_raw)
        codigo_value = codigo or None
        zona_value = smart_title(normalize_text(zona_sanitaria)) if zona_sanitaria else None

        existing = Institucion.query.filter_by(nombre=display_name, localidad=localidad).one_or_none()
        payload = {
            "nombre": display_name,
            "tipo_institucion": "Hospital",
            "codigo": codigo_value,
            "localidad": localidad,
            "provincia": "La Pampa",
            "zona_sanitaria": zona_value,
            "estado": "Activa",
        }

        if existing:
            updated = False
            for field, value in payload.items():
                if getattr(existing, field) != value:
                    setattr(existing, field, value)
                    updated = True
            if updated:
                stats.updated += 1
            else:
                stats.skipped += 1
            institucion = existing
        else:
            institucion = Institucion(**payload)
            db.session.add(institucion)
            db.session.flush()
            stats.created += 1

        ensure_defaults(institucion, stats)
    progress.close()
    return stats


def seed_from_csv(csv_path: Path) -> SeedStats:
    LOGGER.info("Cargando datos desde %s", csv_path)
    rows = read_csv_rows(csv_path)
    if not rows:
        LOGGER.warning("El archivo CSV no contiene registros.")
        return SeedStats()
    stats = process_rows(rows)
    db.session.commit()
    LOGGER.info(
        "Proceso completado. Instituciones creadas=%s, actualizadas=%s, omitidas=%s, servicios creados=%s, oficinas creadas=%s.",
        stats.created,
        stats.updated,
        stats.skipped,
        stats.services_created,
        stats.offices_created,
    )
    return stats


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Importa instituciones sanitarias desde un CSV.")
    parser.add_argument("--csv", required=True, help="Ruta al archivo Contenido.csv a importar.")
    parser.add_argument("--verbose", action="store_true", help="Mostrar mensajes de depuración.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    csv_path = Path(args.csv).expanduser().resolve()
    if not csv_path.is_file():
        parser.error(f"El archivo {csv_path} no existe o no es accesible.")

    configure_logging(args.verbose)

    app = create_app()
    with app.app_context():
        try:
            seed_from_csv(csv_path)
        except Exception as exc:  # pragma: no cover - reporte amigable
            LOGGER.exception("Error al importar instituciones: %s", exc)
            db.session.rollback()
            return 1
    return 0


if __name__ == "__main__":  # pragma: no cover - punto de entrada CLI
    sys.exit(main())
