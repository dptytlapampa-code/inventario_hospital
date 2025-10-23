"""Views to manage VLAN registries and associated devices."""
from __future__ import annotations

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required
from sqlalchemy import false, or_
from sqlalchemy.orm import joinedload, selectinload

from app.extensions import db
from app.forms.vlan import VlanDispositivoForm, VlanForm
from app.models import Hospital, Modulo, Vlan, VlanDispositivo
from app.security import require_roles
from app.services.audit_service import log_action

vlans_bp = Blueprint("vlans", __name__, url_prefix="/vlans")


def _allowed_hospital_ids() -> set[int] | None:
    if current_user.has_role("superadmin"):
        return None
    return current_user.allowed_hospital_ids(Modulo.INVENTARIO.value)


@vlans_bp.route("/")
@login_required
@require_roles("superadmin", "admin", "tecnico")
def listar():
    """Listar las VLAN disponibles de acuerdo al alcance del usuario."""

    buscar = request.args.get("q", "").strip()
    hospital_id = request.args.get("hospital_id", type=int)
    page = request.args.get("page", type=int, default=1)
    per_page = current_app.config.get("DEFAULT_PAGE_SIZE", 20)

    query = Vlan.query.options(joinedload(Vlan.hospital)).order_by(
        Vlan.nombre.asc(), Vlan.identificador.asc()
    )

    allowed = _allowed_hospital_ids()
    if allowed is not None:
        if not allowed:
            query = query.filter(false())
        else:
            query = query.filter(Vlan.hospital_id.in_(allowed))

    if hospital_id:
        query = query.filter(Vlan.hospital_id == hospital_id)

    if buscar:
        like = f"%{buscar}%"
        query = query.filter(
            or_(
                Vlan.nombre.ilike(like),
                Vlan.identificador.ilike(like),
                Vlan.descripcion.ilike(like),
            )
        )

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    hospitales_query = Hospital.query.order_by(Hospital.nombre.asc())
    if allowed is not None:
        if not allowed:
            hospitales_query = hospitales_query.filter(false())
        else:
            hospitales_query = hospitales_query.filter(Hospital.id.in_(allowed))
    hospitales = hospitales_query.all()

    return render_template(
        "vlans/listar.html",
        vlans=pagination.items,
        pagination=pagination,
        hospitales=hospitales,
        hospital_id=hospital_id,
        buscar=buscar,
    )


@vlans_bp.route("/crear", methods=["GET", "POST"])
@login_required
@require_roles("superadmin")
def crear_vlan():
    """Registrar una nueva VLAN."""

    form = VlanForm()
    preset_hospital = request.args.get("hospital_id", type=int)
    if request.method == "GET" and preset_hospital:
        if preset_hospital in {choice[0] for choice in form.hospital_id.choices}:
            form.hospital_id.data = preset_hospital
            form._load_servicio_choices(form.hospital_id.data)
            form._load_oficina_choices(form.hospital_id.data, form.servicio_id.data)
    if form.validate_on_submit():
        vlan = Vlan(
            nombre=form.nombre.data.strip(),
            identificador=form.identificador.data.strip(),
            descripcion=(form.descripcion.data or "").strip() or None,
            hospital_id=form.hospital_id.data,
            servicio_id=form.servicio_id.data or None,
            oficina_id=form.oficina_id.data or None,
        )
        db.session.add(vlan)
        db.session.commit()
        log_action(
            usuario_id=current_user.id,
            accion="crear",
            modulo="vlans",
            tabla="vlans",
            registro_id=vlan.id,
            hospital_id=vlan.hospital_id,
        )
        flash("VLAN creada correctamente.", "success")
        return redirect(url_for("vlans.detalle", vlan_id=vlan.id))
    return render_template("vlans/form_vlan.html", form=form, titulo="Nueva VLAN")


def _ensure_access(vlan: Vlan) -> None:
    allowed = _allowed_hospital_ids()
    if allowed is not None and vlan.hospital_id not in allowed:
        abort(403)


@vlans_bp.route("/<int:vlan_id>")
@login_required
@require_roles("superadmin", "admin", "tecnico")
def detalle(vlan_id: int):
    """Mostrar el detalle de una VLAN y los dispositivos asociados."""

    vlan = (
        Vlan.query.options(
            joinedload(Vlan.hospital),
            selectinload(Vlan.dispositivos).joinedload(VlanDispositivo.hospital),
            selectinload(Vlan.dispositivos).joinedload(VlanDispositivo.oficina),
            selectinload(Vlan.dispositivos).joinedload(VlanDispositivo.servicio),
        )
        .filter_by(id=vlan_id)
        .first_or_404()
    )
    _ensure_access(vlan)

    dispositivos = sorted(
        vlan.dispositivos,
        key=lambda disp: (disp.hospital.nombre.lower(), disp.direccion_ip),
    )

    return render_template(
        "vlans/detalle.html",
        vlan=vlan,
        dispositivos=dispositivos,
    )


@vlans_bp.route("/<int:vlan_id>/editar", methods=["GET", "POST"])
@login_required
@require_roles("superadmin")
def editar_vlan(vlan_id: int):
    """Permitir la edición de una VLAN existente."""

    vlan = Vlan.query.get_or_404(vlan_id)
    form = VlanForm(vlan=vlan, obj=vlan)
    if form.validate_on_submit():
        vlan.nombre = form.nombre.data.strip()
        vlan.identificador = form.identificador.data.strip()
        vlan.descripcion = (form.descripcion.data or "").strip() or None
        vlan.hospital_id = form.hospital_id.data
        vlan.servicio_id = form.servicio_id.data or None
        vlan.oficina_id = form.oficina_id.data or None
        db.session.commit()
        log_action(
            usuario_id=current_user.id,
            accion="actualizar",
            modulo="vlans",
            tabla="vlans",
            registro_id=vlan.id,
            hospital_id=vlan.hospital_id,
        )
        flash("VLAN actualizada correctamente.", "success")
        return redirect(url_for("vlans.detalle", vlan_id=vlan.id))
    return render_template(
        "vlans/form_vlan.html",
        form=form,
        titulo="Editar VLAN",
        vlan=vlan,
    )


@vlans_bp.route("/<int:vlan_id>/eliminar", methods=["POST"])
@login_required
@require_roles("superadmin")
def eliminar_vlan(vlan_id: int):
    """Eliminar una VLAN y sus dispositivos."""

    vlan = Vlan.query.get_or_404(vlan_id)
    db.session.delete(vlan)
    db.session.commit()
    log_action(
        usuario_id=current_user.id,
        accion="eliminar",
        modulo="vlans",
        tabla="vlans",
        registro_id=vlan.id,
        hospital_id=vlan.hospital_id,
    )
    flash("VLAN eliminada.", "success")
    return redirect(url_for("vlans.listar"))


@vlans_bp.route("/<int:vlan_id>/dispositivos/crear", methods=["GET", "POST"])
@login_required
@require_roles("superadmin")
def crear_dispositivo(vlan_id: int):
    """Registrar un nuevo dispositivo asociado a una VLAN."""

    vlan = Vlan.query.get_or_404(vlan_id)
    form = VlanDispositivoForm(vlan=vlan)
    if form.validate_on_submit():
        dispositivo = VlanDispositivo(
            vlan_id=form.vlan_id.data,
            nombre_equipo=form.nombre_equipo.data.strip(),
            host=(form.host.data or "").strip() or None,
            direccion_ip=form.direccion_ip.data.strip(),
            direccion_mac=(form.direccion_mac.data or "").strip() or None,
            hospital_id=form.hospital_id.data,
            servicio_id=form.servicio_id.data or None,
            oficina_id=form.oficina_id.data or None,
            notas=(form.notas.data or "").strip() or None,
        )
        db.session.add(dispositivo)
        db.session.commit()
        log_action(
            usuario_id=current_user.id,
            accion="crear",
            modulo="vlans",
            tabla="vlan_dispositivos",
            registro_id=dispositivo.id,
            hospital_id=dispositivo.hospital_id,
        )
        flash("Dispositivo registrado correctamente.", "success")
        return redirect(url_for("vlans.detalle", vlan_id=dispositivo.vlan_id))
    return render_template(
        "vlans/form_dispositivo.html",
        form=form,
        titulo="Nuevo dispositivo",
        vlan=vlan,
    )


@vlans_bp.route("/dispositivos/<int:dispositivo_id>/editar", methods=["GET", "POST"])
@login_required
@require_roles("superadmin")
def editar_dispositivo(dispositivo_id: int):
    """Editar un dispositivo existente."""

    dispositivo = (
        VlanDispositivo.query.options(joinedload(VlanDispositivo.vlan))
        .filter_by(id=dispositivo_id)
        .first_or_404()
    )
    form = VlanDispositivoForm(dispositivo=dispositivo, obj=dispositivo)
    if form.validate_on_submit():
        dispositivo.vlan_id = form.vlan_id.data
        dispositivo.nombre_equipo = form.nombre_equipo.data.strip()
        dispositivo.host = (form.host.data or "").strip() or None
        dispositivo.direccion_ip = form.direccion_ip.data.strip()
        dispositivo.direccion_mac = (form.direccion_mac.data or "").strip() or None
        dispositivo.hospital_id = form.hospital_id.data
        dispositivo.servicio_id = form.servicio_id.data or None
        dispositivo.oficina_id = form.oficina_id.data or None
        dispositivo.notas = (form.notas.data or "").strip() or None
        db.session.commit()
        log_action(
            usuario_id=current_user.id,
            accion="actualizar",
            modulo="vlans",
            tabla="vlan_dispositivos",
            registro_id=dispositivo.id,
            hospital_id=dispositivo.hospital_id,
        )
        flash("Dispositivo actualizado correctamente.", "success")
        return redirect(url_for("vlans.detalle", vlan_id=dispositivo.vlan_id))
    return render_template(
        "vlans/form_dispositivo.html",
        form=form,
        titulo="Editar dispositivo",
        dispositivo=dispositivo,
        vlan=dispositivo.vlan,
    )


@vlans_bp.route("/dispositivos/<int:dispositivo_id>/eliminar", methods=["POST"])
@login_required
@require_roles("superadmin")
def eliminar_dispositivo(dispositivo_id: int):
    """Eliminar un dispositivo de la VLAN."""

    dispositivo = VlanDispositivo.query.get_or_404(dispositivo_id)
    vlan_id = dispositivo.vlan_id
    db.session.delete(dispositivo)
    db.session.commit()
    log_action(
        usuario_id=current_user.id,
        accion="eliminar",
        modulo="vlans",
        tabla="vlan_dispositivos",
        registro_id=dispositivo.id,
        hospital_id=dispositivo.hospital_id,
    )
    flash("Dispositivo eliminado.", "success")
    return redirect(url_for("vlans.detalle", vlan_id=vlan_id))


__all__ = ["vlans_bp"]
