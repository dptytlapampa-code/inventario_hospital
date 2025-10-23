"""Colección de formularios reutilizables en la aplicación."""

from .acta import ActaForm
from .adjunto import AdjuntoForm
from .docscan import DocscanForm
from .equipo import EquipoForm
from .hospital import HospitalForm
from .insumo import InsumoForm
from .licencia import LicenciaForm  # type: ignore F401 - legacy import
from .login import LoginForm  # type: ignore F401 - legacy import
from .permisos import PermisoForm
from .usuario import UsuarioForm
from .vlan import VlanDispositivoForm, VlanForm

__all__ = [
    "ActaForm",
    "AdjuntoForm",
    "DocscanForm",
    "EquipoForm",
    "HospitalForm",
    "InsumoForm",
    "LicenciaForm",
    "LoginForm",
    "PermisoForm",
    "UsuarioForm",
    "VlanForm",
    "VlanDispositivoForm",
]
