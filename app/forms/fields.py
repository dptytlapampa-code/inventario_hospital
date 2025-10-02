"""Custom WTForms field helpers used across the project."""
from __future__ import annotations

from typing import Iterable

from wtforms import HiddenField


class HiddenIntegerField(HiddenField):
    """Hidden field that coerces submitted values into integers."""

    def process_data(self, value: int | str | None) -> None:  # type: ignore[override]
        if value is None or value == "":
            self.data = None
            return
        try:
            self.data = int(value)
        except (TypeError, ValueError):
            self.data = None

    def process_formdata(self, valuelist: list[str]) -> None:  # type: ignore[override]
        if not valuelist:
            self.data = None
            return
        raw = (valuelist[0] or "").strip()
        if not raw:
            self.data = None
            return
        try:
            self.data = int(raw)
        except ValueError:
            self.data = None

    def _value(self) -> str:  # type: ignore[override]
        return "" if self.data is None else str(self.data)


class CSVIntegerListField(HiddenField):
    """Hidden field that serialises a list of integers using commas."""

    def process_data(self, value: Iterable[int] | str | None) -> None:  # type: ignore[override]
        if value is None:
            self.data = []
            return
        if isinstance(value, str):
            self.data = self._parse_string(value)
            return
        items: list[int] = []
        for item in value:
            try:
                coerced = int(item)
            except (TypeError, ValueError):
                continue
            if coerced not in items:
                items.append(coerced)
        self.data = items

    def process_formdata(self, valuelist: list[str]) -> None:  # type: ignore[override]
        if not valuelist:
            self.data = []
            return
        raw = (valuelist[0] or "").strip()
        if not raw:
            self.data = []
            return
        self.data = self._parse_string(raw)

    @staticmethod
    def _parse_string(raw: str) -> list[int]:
        values: list[int] = []
        for chunk in raw.split(","):
            piece = chunk.strip()
            if not piece:
                continue
            try:
                value = int(piece)
            except ValueError:
                continue
            if value not in values:
                values.append(value)
        return values

    def _value(self) -> str:  # type: ignore[override]
        if not self.data:
            return ""
        return ",".join(str(item) for item in self.data)


__all__ = ["HiddenIntegerField", "CSVIntegerListField"]
