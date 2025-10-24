from __future__ import annotations

from io import BytesIO
from zipfile import ZipFile
import xml.etree.ElementTree as ET


def login(client, username: str, password: str) -> None:
    client.post("/auth/login", data={"username": username, "password": password}, follow_redirects=True)


def test_export_requires_superadmin(client, admin_credentials):
    login(client, **admin_credentials)
    resp = client.get("/reportes/exportar")
    assert resp.status_code == 403


def test_superadmin_can_download_report(client, superadmin_credentials):
    login(client, **superadmin_credentials)
    resp = client.get("/reportes/exportar/descargar")
    assert resp.status_code == 200
    assert (
        resp.headers["Content-Type"]
        == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    sheet_names = _extract_sheet_names(resp.data)
    expected_sheets = {
        "Instituciones",
        "Equipos",
        "Insumos",
        "Usuarios",
        "VLANs",
        "VLAN Dispositivos",
    }
    assert expected_sheets.issubset(set(sheet_names))


def test_export_filters_by_hospital(client, superadmin_credentials, data):
    login(client, **superadmin_credentials)
    hospital = data["hospital_secundario"]
    resp = client.get(f"/reportes/exportar/descargar?hospital_id={hospital.id}")
    assert resp.status_code == 200
    rows = _read_sheet(resp.data, "Equipos")
    hospitales = {row[0] for row in rows[1:] if row and row[0]}
    assert hospitales == {hospital.nombre}


def _extract_sheet_names(data: bytes) -> list[str]:
    with ZipFile(BytesIO(data)) as archive:
        workbook_xml = archive.read("xl/workbook.xml")
    ns = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    root = ET.fromstring(workbook_xml)
    return [
        sheet.attrib.get("name", "")
        for sheet in root.findall("main:sheets/main:sheet", ns)
    ]


def _read_sheet(data: bytes, sheet_name: str) -> list[list[str]]:
    ns = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with ZipFile(BytesIO(data)) as archive:
        workbook_xml = archive.read("xl/workbook.xml")
        workbook_root = ET.fromstring(workbook_xml)
        sheet_index = None
        for index, sheet in enumerate(
            workbook_root.findall("main:sheets/main:sheet", ns), start=1
        ):
            if sheet.attrib.get("name") == sheet_name:
                sheet_index = index
                break
        if sheet_index is None:
            return []
        shared_strings = []
        if "xl/sharedStrings.xml" in archive.namelist():
            shared_root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            shared_strings = [
                (si.find("main:t", ns).text or "")
                for si in shared_root.findall("main:si", ns)
            ]
        sheet_root = ET.fromstring(
            archive.read(f"xl/worksheets/sheet{sheet_index}.xml")
        )
    rows: list[list[str]] = []
    for row in sheet_root.findall("main:sheetData/main:row", ns):
        current_row: list[str] = []
        for cell in row.findall("main:c", ns):
            ref = cell.attrib.get("r", "")
            col_letters = "".join(ch for ch in ref if ch.isalpha())
            col_index = _column_index(col_letters)
            while len(current_row) < col_index:
                current_row.append("")
            value_element = cell.find("main:v", ns)
            if value_element is None:
                current_row[col_index - 1] = ""
            elif cell.attrib.get("t") == "s":
                idx = int(value_element.text or "0")
                current_row[col_index - 1] = shared_strings[idx] if idx < len(shared_strings) else ""
            else:
                current_row[col_index - 1] = value_element.text or ""
        rows.append(current_row)
    return rows


def _column_index(letters: str) -> int:
    result = 0
    for char in letters:
        if not char:
            continue
        result = result * 26 + (ord(char.upper()) - 64)
    return max(result, 1)
