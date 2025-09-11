from typing import Dict, Optional

try:  # pragma: no cover - fallbacks for environments without Flask
    from flask import (
        Blueprint,
        flash,
        redirect,
        render_template,
        url_for,
        current_app,
    )
    from flask_login import login_required
    from app.security import permissions_required
except ModuleNotFoundError:  # pragma: no cover - simple stubs for testing
    class Blueprint:  # type: ignore
        def __init__(self, *args, **kwargs) -> None:
            pass

        def route(self, *args, **kwargs):
            def decorator(func):
                return func

            return decorator

    def flash(*args, **kwargs):
        return None

    def redirect(location):  # type: ignore
        return location

    def render_template(template_name: str, **context):  # type: ignore
        return template_name

    def url_for(endpoint: str, **values):  # type: ignore
        return endpoint

    def login_required(func):  # type: ignore
        return func

    def permissions_required(*_args, **_kwargs):  # type: ignore
        def decorator(func):
            return func

        return decorator

    current_app = None  # type: ignore

try:
    from app.forms.licencia import AprobarRechazarForm, LicenciaForm
except ModuleNotFoundError:  # pragma: no cover - simple stubs for tests
    AprobarRechazarForm = LicenciaForm = None  # type: ignore
from licencias import Licencia


licencias_bp = Blueprint("licencias", __name__, url_prefix="/licencias")


# Simple in-memory storage for demo purposes using a dict keyed by ID
SOLICITUDES: Dict[int, Licencia] = {}


def _get_solicitud(licencia_id: int) -> Optional[Licencia]:
    """Retrieve a stored request by its identifier."""
    return SOLICITUDES.get(licencia_id)


@licencias_bp.route("/solicitar", methods=["GET", "POST"])
@login_required
@permissions_required("licencias:write")
def solicitar():
    form = LicenciaForm()
    if form.validate_on_submit():
        licencia_id = max(SOLICITUDES.keys(), default=0) + 1
        licencia = Licencia(
            usuario_id=int(form.empleado.data),
            fecha_inicio=form.fecha_inicio.data,
            fecha_fin=form.fecha_fin.data,
            requires_replacement=form.requiere_reemplazo.data,
            reemplazo_id=form.reemplazo_id.data,
        )
        licencia.enviar_pendiente()
        SOLICITUDES[licencia_id] = licencia

        # Attempt to persist using SQLAlchemy if a DB session is available
        try:  # pragma: no cover - optional DB integration
            if current_app and current_app.config.get("db_session"):
                from app.models.licencia import (
                    EstadoLicencia as EstadoDB,
                    Licencia as LicenciaDB,
                    TipoLicencia,
                )

                session = current_app.config["db_session"]
                registro = LicenciaDB(
                    usuario_id=licencia.usuario_id,
                    hospital_id=None,
                    tipo=TipoLicencia.TEMPORAL,
                    estado=EstadoDB.ACTIVA,
                    requires_replacement=licencia.requires_replacement,
                )
                session.add(registro)
                session.commit()
        except Exception:
            # Silently ignore persistence errors in this simplified example
            pass

        flash("Solicitud registrada", "success")
        return redirect(url_for("licencias.listar"))
    return render_template("licencias/solicitar.html", form=form)


@licencias_bp.route("/listar")
@login_required
@permissions_required("licencias:read")
def listar():
    return render_template("licencias/listar.html", solicitudes=list(SOLICITUDES.values()))


@licencias_bp.route("/<int:licencia_id>/aprobar_rechazar", methods=["GET", "POST"])
@login_required
@permissions_required("licencias:write")
def aprobar_rechazar(licencia_id: int):
    solicitud = _get_solicitud(licencia_id)
    if not solicitud:
        flash("Solicitud no encontrada", "error")
        return redirect(url_for("licencias.listar"))

    form = AprobarRechazarForm()
    if form.validate_on_submit():
        accion = form.accion.data
        if accion == "aprobar":
            solicitud.aprobar()
        else:
            solicitud.rechazar()
        flash(f"Solicitud {accion}da", "success")
        return redirect(url_for("licencias.detalle", licencia_id=licencia_id))
    return render_template(
        "licencias/aprobar_rechazar.html", form=form, solicitud=solicitud
    )


@licencias_bp.route("/calendario")
@login_required
@permissions_required("licencias:read")
def calendario():
    return render_template("licencias/calendario.html", solicitudes=list(SOLICITUDES.values()))


@licencias_bp.route("/<int:licencia_id>/detalle")
@login_required
@permissions_required("licencias:read")
def detalle(licencia_id: int):
    solicitud = _get_solicitud(licencia_id)
    if not solicitud:
        flash("Solicitud no encontrada", "error")
        return redirect(url_for("licencias.listar"))
    return render_template("licencias/detalle.html", solicitud=solicitud)
