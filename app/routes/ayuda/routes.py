"""Vistas del módulo de ayuda y orientación por rol."""
from __future__ import annotations

from flask import Blueprint, render_template
from flask_login import current_user, login_required

ayuda_bp = Blueprint("ayuda", __name__, url_prefix="/ayuda")

HELP_SECTIONS: list[dict[str, object]] = [
    {
        "role": "superadmin",
        "title": "SuperAdmin",
        "summary": (
            "Rol con acceso total al inventario para configurar catálogos, gestionar permisos y"
            " definir la estructura general del sistema."
        ),
        "areas": [
            {
                "title": "Dashboard",
                "description": (
                    "Visión general de equipos, insumos y licencias con métricas en tiempo real para"
                    " detectar desvíos rápidamente."
                ),
            },
            {
                "title": "Gestión de licencias",
                "description": (
                    "Acceso completo al flujo de licencias para aprobar, reasignar y crear nuevas"
                    " licencias para toda la organización."
                ),
                "items": [
                    "Panel de gestión para revisar solicitudes pendientes y su historial.",
                    "Carga manual de nuevas licencias o importación desde archivos.",
                    "Definición de tipos de licencia y estados personalizados según la política institucional.",
                ],
            },
            {
                "title": "Equipos",
                "description": (
                    "Administración integral del parque informático y biomédico."
                ),
                "items": [
                    "Alta y baja de equipos, incluyendo asignación de responsables y ubicaciones.",
                    "Gestión de tipos de equipo y catálogos de modelos.",
                    "Carga y consulta de adjuntos, actas de entrega y documentos escaneados.",
                ],
            },
            {
                "title": "Insumos",
                "description": (
                    "Control de stock, reposiciones y seguimiento de insumos críticos."
                ),
                "items": [
                    "Consulta de existencias generales y filtros por elementos críticos.",
                    "Registro de movimientos y creación de nuevos insumos."
                ],
            },
            {
                "title": "Ubicaciones",
                "description": (
                    "Organización jerárquica de hospitales, servicios y oficinas disponibles para los equipos."
                ),
                "items": [
                    "Alta y edición de hospitales, servicios y oficinas.",
                    "Asignación de responsables por hospital para seguimiento operativo.",
                ],
            },
            {
                "title": "Usuarios y permisos",
                "description": (
                    "Configuración de roles, auditorías y alcances de acceso."
                ),
                "items": [
                    "Creación y edición de usuarios del sistema.",
                    "Definición de permisos por rol y hospital.",
                    "Revisión de auditorías y asignaciones de hospitales.",
                ],
            },
            {
                "title": "VLANs",
                "description": (
                    "Administración de segmentación de red para equipos conectados."
                ),
                "items": [
                    "Alta de nuevas VLANs, incluyendo sus rangos de IP.",
                    "Consulta del inventario actual y dispositivos asociados."
                ],
            },
        ],
        "tips": [
            "Utilizá este rol para configurar la estructura inicial del sistema y delegar tareas en administradores.",
            "Revisá periódicamente la auditoría para detectar cambios inusuales en inventarios o permisos.",
        ],
    },
    {
        "role": "admin",
        "title": "Admin",
        "summary": (
            "Rol orientado a la operación diaria: mantiene datos de equipos e insumos y supervisa el personal"
            " asignado sin necesidad de modificar catálogos globales."
        ),
        "areas": [
            {
                "title": "Dashboard",
                "description": "Indicadores clave de equipos, licencias e insumos para tu área de gestión.",
            },
            {
                "title": "Licencias",
                "description": (
                    "Consulta tus licencias y accedé al panel de gestión para aprobar o derivar solicitudes de tu ámbito."
                ),
            },
            {
                "title": "Equipos",
                "description": "Actualización del inventario operativo.",
                "items": [
                    "Alta y edición de equipos existentes.",
                    "Carga de adjuntos y actas relacionadas.",
                    "Consulta de documentos escaneados para respaldos técnicos.",
                ],
            },
            {
                "title": "Insumos",
                "description": "Seguimiento de stock y alertas de insumos críticos.",
                "items": [
                    "Revisión rápida de insumos críticos para coordinar compras.",
                    "Registro de ingresos o egresos según corresponda a tu permiso.",
                ],
            },
            {
                "title": "Ubicaciones",
                "description": "Mantenimiento de la estructura de hospitales, servicios y oficinas dentro de tu jurisdicción.",
            },
            {
                "title": "Usuarios y auditoría",
                "description": "Supervisión del personal técnico y seguimiento de actividades.",
                "items": [
                    "Alta de nuevos técnicos o administrativos.",
                    "Gestión de permisos disponibles para el rol.",
                    "Consulta de auditorías para revisar acciones recientes.",
                ],
            },
            {
                "title": "VLANs",
                "description": "Visualización del esquema de red y asociaciones disponibles.",
                "items": [
                    "Consulta de VLANs habilitadas.",
                    "Verificación de dispositivos asignados a cada segmento.",
                ],
            },
        ],
        "tips": [
            "Coordiná con el SuperAdmin cuando necesites nuevos tipos de equipo o cambios estructurales.",
            "Documentá en actas cualquier traspaso relevante para mantener la trazabilidad.",
        ],
    },
    {
        "role": "tecnico",
        "title": "Técnico",
        "summary": (
            "Rol centrado en la ejecución: permite consultar inventarios, registrar novedades básicas y seguir tus licencias"
            " asignadas."
        ),
        "areas": [
            {
                "title": "Dashboard",
                "description": "Resumen de tus pendientes y del estado general del inventario que tenés asignado.",
            },
            {
                "title": "Licencias personales",
                "description": "Consulta y seguimiento de tus licencias vigentes o solicitudes en curso.",
            },
            {
                "title": "Equipos",
                "description": "Acceso al listado completo y a la ficha de cada equipo.",
                "items": [
                    "Consulta de datos técnicos, responsable y ubicación.",
                    "Registro de nuevas intervenciones si tu permiso lo habilita.",
                    "Carga y consulta de adjuntos como manuales o fotografías.",
                ],
            },
            {
                "title": "Actas y documentación",
                "description": "Acceso rápido a actas y documentos escaneados vinculados a tus tareas.",
            },
            {
                "title": "Insumos",
                "description": "Revisión del stock disponible para preparar intervenciones y detectar faltantes.",
                "items": [
                    "Filtro específico para insumos críticos.",
                    "Carga de consumos si contás con permiso de escritura.",
                ],
            },
            {
                "title": "VLANs",
                "description": "Consulta de redes disponibles para conectar o diagnosticar equipos.",
            },
        ],
        "tips": [
            "Actualizá adjuntos y notas técnicas para mantener al equipo informado.",
            "Si necesitás permisos adicionales, solicitá a un administrador que revise tu rol.",
        ],
    },
]


@ayuda_bp.get("/")
@login_required
def index() -> str:
    """Mostrar la guía de ayuda general por rol."""

    current_role = current_user.role or ""
    return render_template(
        "ayuda/index.html",
        help_sections=HELP_SECTIONS,
        current_role=current_role,
    )
