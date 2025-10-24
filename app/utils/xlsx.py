"""Utilidad mínima para generar archivos XLSX sin dependencias externas."""

from __future__ import annotations

import itertools
from dataclasses import dataclass
from datetime import datetime, timezone
from io import BytesIO
from typing import Iterable
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZipFile


def _column_letter(index: int) -> str:
    result = []
    while index > 0:
        index, remainder = divmod(index - 1, 26)
        result.append(chr(65 + remainder))
    return "".join(reversed(result)) or "A"


@dataclass
class Sheet:
    name: str
    rows: list[list[object]]


class SimpleXLSX:
    """Generador básico de archivos XLSX usando solo la librería estándar."""

    def __init__(self) -> None:
        self._sheets: list[Sheet] = []

    def add_sheet(self, title: str, rows: Iterable[Iterable[object]]) -> None:
        safe_title = (title or "Sheet").strip()[:31] or "Sheet"
        counter = 1
        existing = {sheet.name for sheet in self._sheets}
        candidate = safe_title
        while candidate in existing:
            counter += 1
            candidate = f"{safe_title[:28]}-{counter}" if len(safe_title) > 28 else f"{safe_title}-{counter}"
        matrix = [list(row) for row in rows]
        self._sheets.append(Sheet(candidate, matrix))

    def to_bytes(self) -> BytesIO:
        if not self._sheets:
            raise ValueError("Debe agregarse al menos una hoja antes de exportar")

        shared_strings: list[str] = []
        string_index: dict[str, int] = {}
        for sheet in self._sheets:
            for value in itertools.chain.from_iterable(sheet.rows):
                if isinstance(value, (int, float)) or value is None:
                    continue
                text = str(value)
                if text not in string_index:
                    string_index[text] = len(shared_strings)
                    shared_strings.append(text)

        timestamp = (
            datetime.now(timezone.utc)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z")
        )

        buffer = BytesIO()
        with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
            archive.writestr(
                "[Content_Types].xml",
                _build_content_types(len(self._sheets)),
            )
            archive.writestr(
                "_rels/.rels",
                _build_rels(),
            )
            archive.writestr(
                "docProps/app.xml",
                _build_app_props(self._sheets),
            )
            archive.writestr(
                "docProps/core.xml",
                _build_core_props(timestamp),
            )
            archive.writestr(
                "xl/workbook.xml",
                _build_workbook(self._sheets),
            )
            archive.writestr(
                "xl/_rels/workbook.xml.rels",
                _build_workbook_rels(len(self._sheets)),
            )
            archive.writestr("xl/styles.xml", _build_styles())
            archive.writestr(
                "xl/sharedStrings.xml",
                _build_shared_strings(shared_strings),
            )
            for index, sheet in enumerate(self._sheets, start=1):
                archive.writestr(
                    f"xl/worksheets/sheet{index}.xml",
                    _build_sheet(sheet.rows, string_index),
                )

        buffer.seek(0)
        return buffer


def _build_content_types(sheet_count: int) -> str:
    overrides = "".join(
        f'<Override PartName="/xl/worksheets/sheet{index}.xml" '
        "ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml\"/>"
        for index in range(1, sheet_count + 1)
    )
    return (
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
        "<Types xmlns=\"http://schemas.openxmlformats.org/package/2006/content-types\">"
        "<Default Extension=\"rels\" ContentType=\"application/vnd.openxmlformats-package.relationships+xml\"/>"
        "<Default Extension=\"xml\" ContentType=\"application/xml\"/>"
        "<Override PartName=\"/xl/workbook.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml\"/>"
        "<Override PartName=\"/xl/styles.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml\"/>"
        "<Override PartName=\"/xl/sharedStrings.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml\"/>"
        "<Override PartName=\"/docProps/core.xml\" ContentType=\"application/vnd.openxmlformats-package.core-properties+xml\"/>"
        "<Override PartName=\"/docProps/app.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.extended-properties+xml\"/>"
        f"{overrides}"
        "</Types>"
    )


def _build_rels() -> str:
    return (
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
        "<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">"
        "<Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument\" Target=\"xl/workbook.xml\"/>"
        "<Relationship Id=\"rId2\" Type=\"http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties\" Target=\"docProps/core.xml\"/>"
        "<Relationship Id=\"rId3\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties\" Target=\"docProps/app.xml\"/>"
        "</Relationships>"
    )


def _build_app_props(sheets: list[Sheet]) -> str:
    titles = "".join(f"<vt:lpstr>{escape(sheet.name)}</vt:lpstr>" for sheet in sheets)
    count = len(sheets)
    return (
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
        "<Properties xmlns=\"http://schemas.openxmlformats.org/officeDocument/2006/extended-properties\" xmlns:vt=\"http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes\">"
        "<Application>Inventario Hospital</Application>"
        "<DocSecurity>0</DocSecurity>"
        "<ScaleCrop>false</ScaleCrop>"
        "<HeadingPairs><vt:vector size=\"2\" baseType=\"variant\"><vt:variant><vt:lpstr>Worksheets</vt:lpstr></vt:variant><vt:variant><vt:i4>"
        f"{count}"
        "</vt:i4></vt:variant></vt:vector></HeadingPairs>"
        f"<TitlesOfParts><vt:vector size=\"{count}\" baseType=\"lpstr\">{titles}</vt:vector></TitlesOfParts>"
        "</Properties>"
    )


def _build_core_props(timestamp: str) -> str:
    return (
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
        "<cp:coreProperties xmlns:cp=\"http://schemas.openxmlformats.org/package/2006/metadata/core-properties\" xmlns:dc=\"http://purl.org/dc/elements/1.1/\" xmlns:dcterms=\"http://purl.org/dc/terms/\" xmlns:dcmitype=\"http://purl.org/dc/dcmitype/\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\">"
        "<dc:creator>Inventario Hospital</dc:creator>"
        "<cp:lastModifiedBy>Inventario Hospital</cp:lastModifiedBy>"
        f"<dcterms:created xsi:type=\"dcterms:W3CDTF\">{timestamp}</dcterms:created>"
        f"<dcterms:modified xsi:type=\"dcterms:W3CDTF\">{timestamp}</dcterms:modified>"
        "</cp:coreProperties>"
    )


def _build_workbook(sheets: list[Sheet]) -> str:
    sheet_entries = "".join(
        f'<sheet name="{escape(sheet.name)}" sheetId="{index}" r:id="rId{index}"/>'
        for index, sheet in enumerate(sheets, start=1)
    )
    return (
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
        "<workbook xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\" xmlns:r=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships\">"
        f"<sheets>{sheet_entries}</sheets>"
        "</workbook>"
    )


def _build_workbook_rels(sheet_count: int) -> str:
    relationships = []
    for index in range(1, sheet_count + 1):
        relationships.append(
            f'<Relationship Id="rId{index}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{index}.xml"/>'
        )
    relationships.append(
        f'<Relationship Id="rId{sheet_count + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
    )
    relationships.append(
        f'<Relationship Id="rId{sheet_count + 2}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings" Target="sharedStrings.xml"/>'
    )
    rels_xml = "".join(relationships)
    return (
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
        "<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">"
        f"{rels_xml}</Relationships>"
    )


def _build_styles() -> str:
    return (
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
        "<styleSheet xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\">"
        "<fonts count=\"1\"><font><sz val=\"11\"/><color theme=\"1\"/><name val=\"Calibri\"/><family val=\"2\"/></font></fonts>"
        "<fills count=\"1\"><fill><patternFill patternType=\"none\"/></fill></fills>"
        "<borders count=\"1\"><border><left/><right/><top/><bottom/><diagonal/></border></borders>"
        "<cellStyleXfs count=\"1\"><xf numFmtId=\"0\" fontId=\"0\" fillId=\"0\" borderId=\"0\"/></cellStyleXfs>"
        "<cellXfs count=\"1\"><xf numFmtId=\"0\" fontId=\"0\" fillId=\"0\" borderId=\"0\" xfId=\"0\"/></cellXfs>"
        "<cellStyles count=\"1\"><cellStyle name=\"Normal\" xfId=\"0\" builtinId=\"0\"/></cellStyles>"
        "</styleSheet>"
    )


def _build_shared_strings(strings: list[str]) -> str:
    items = "".join(f"<si><t>{escape(text)}</t></si>" for text in strings)
    count = len(strings)
    return (
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
        f"<sst xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\" count=\"{count}\" uniqueCount=\"{count}\">"
        f"{items}</sst>"
    )


def _build_sheet(rows: list[list[object]], string_index: dict[str, int]) -> str:
    row_xml_parts: list[str] = []
    for row_number, row in enumerate(rows, start=1):
        cells = []
        for column_number, value in enumerate(row, start=1):
            if value is None or value == "":
                continue
            cell_ref = f"{_column_letter(column_number)}{row_number}"
            if isinstance(value, (int, float)):
                cell_xml = f"<c r=\"{cell_ref}\"><v>{value}</v></c>"
            else:
                text = str(value)
                index = string_index[text]
                cell_xml = f"<c r=\"{cell_ref}\" t=\"s\"><v>{index}</v></c>"
            cells.append(cell_xml)
        if cells:
            row_xml_parts.append(f"<row r=\"{row_number}\">{''.join(cells)}</row>")
        else:
            row_xml_parts.append(f"<row r=\"{row_number}\"/>")
    rows_xml = "".join(row_xml_parts)
    return (
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
        "<worksheet xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\">"
        f"<sheetData>{rows_xml}</sheetData>"
        "</worksheet>"
    )


__all__ = ["SimpleXLSX"]
