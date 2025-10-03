"""Helpers to manage evidence files stored on disk."""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Iterable, Iterator

from flask import current_app

try:  # pragma: no cover - dependency optional in some environments
    from PIL import Image, ImageFile  # type: ignore
except ImportError:  # pragma: no cover - gracefully fallback when Pillow missing
    Image = None  # type: ignore
    ImageFile = None  # type: ignore


THUMBNAIL_SIZE = (300, 300)
THUMBNAIL_SUFFIX = "_thumb.webp"


def equipment_upload_dir(equipo_id: int) -> Path:
    """Return the upload directory for a given equipment id."""

    base = Path(current_app.config["EQUIPOS_UPLOAD_FOLDER"])
    base.mkdir(parents=True, exist_ok=True)
    target = base / str(equipo_id)
    target.mkdir(parents=True, exist_ok=True)
    return target


def resolve_storage_path(filepath: str) -> Path:
    """Resolve ``filepath`` ensuring it stays inside the configured directory."""

    configured = Path(current_app.config["EQUIPOS_UPLOAD_FOLDER"]).resolve()
    stored = Path(filepath)
    if not stored.is_absolute():
        stored = configured / stored
    stored = stored.resolve()
    if configured not in stored.parents and stored != configured:
        raise FileNotFoundError("Ubicación fuera del directorio permitido")
    return stored


def thumbnail_path(original: Path) -> Path:
    """Return the expected thumbnail path for ``original``."""

    return original.with_name(original.stem + THUMBNAIL_SUFFIX)


@contextmanager
def _open_image_tolerant(path: Path) -> Iterator["Image.Image"]:
    """Open ``path`` tolerating truncated images when Pillow is available."""

    if Image is None:
        yield None  # type: ignore[misc]
        return

    previous_flag = None
    if ImageFile is not None and hasattr(ImageFile, "LOAD_TRUNCATED_IMAGES"):
        previous_flag = ImageFile.LOAD_TRUNCATED_IMAGES  # type: ignore[attr-defined]
        ImageFile.LOAD_TRUNCATED_IMAGES = True  # type: ignore[attr-defined]

    try:
        with Image.open(path) as img:  # pragma: no cover - depends on Pillow
            yield img
    finally:
        if ImageFile is not None and previous_flag is not None and hasattr(ImageFile, "LOAD_TRUNCATED_IMAGES"):
            ImageFile.LOAD_TRUNCATED_IMAGES = previous_flag  # type: ignore[attr-defined]


def generate_image_thumbnail(original: Path) -> Path | None:
    """Generate a WEBP thumbnail for ``original`` if it is an image."""

    if not original.exists():
        return None

    thumb = thumbnail_path(original)
    try:
        if Image is None:
            current_app.logger.warning(
                "Pillow no está instalado; se omite la generación de miniatura para %s.",
                original,
            )
            return None

        with _open_image_tolerant(original) as image:
            if image is None:
                return None
            image = image.convert("RGB")
            image.thumbnail(THUMBNAIL_SIZE)
            thumb.parent.mkdir(parents=True, exist_ok=True)
            image.save(thumb, "WEBP", quality=85, method=6)
    except (OSError, ValueError, SyntaxError) as exc:
        current_app.logger.warning("No se pudo generar miniatura para %s: %s", original, exc)
        return None
    return thumb


def purge_file_variants(paths: Iterable[Path]) -> None:
    """Remove all ``paths`` from disk ignoring missing files."""

    for candidate in paths:
        try:
            candidate.unlink(missing_ok=True)
        except OSError:
            current_app.logger.debug("No se pudo eliminar %s", candidate)


__all__ = [
    "equipment_upload_dir",
    "resolve_storage_path",
    "thumbnail_path",
    "generate_image_thumbnail",
    "purge_file_variants",
]
