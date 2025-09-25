"""Routes to manage role permissions."""
from __future__ import annotations

from collections.abc import Iterable

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.forms.permisos import PermisoForm
from app.models import Hospital, Modulo, Permiso, Rol, Usuario
from app.security import permissions_required
from app.services.audit_service import log_action

permisos_bp = Blueprint("permisos", __name__, url_prefix="/permisos")


def _require_superadmin() -> bool:
    if not current_user.has_role("Superadmin"):
        flash("Solo el Superadmin puede modificar permisos", "warning")
        return False
    return True


def _format_module_label(modulo: Modulo) -> str:
    value = modulo.value.replace("_", " ")
    return value[:1].upper() + value[1:]


def _serialize_permissions(permisos: Iterable[Permiso]) -> dict[str, object]:
    modules = {
        modulo.value: {
            "can_read": False,
            "can_write": False,
            "allow_export": False,
        }
        for modulo in Modulo
    }
    hospitals: set[int] = set()
    for permiso in permisos:
        hospitals.add(0 if permiso.hospital_id is None else permiso.hospital_id)
        module_entry = modules[permiso.modulo.value]
        module_entry["can_read"] = module_entry["can_read"] or permiso.can_read
        module_entry["can_write"] = module_entry["can_write"] or permiso.can_write
        module_entry["allow_export"] = module_entry["allow_export"] or permiso.allow_export
    return {
        "hospitals": sorted(hospitals),
        "modules": modules,
    }


def _serialize_usuario(usuario: Usuario) -> dict[str, object]:
    data = _serialize_permissions(usuario.rol.permisos if usuario.rol else [])
    if usuario.hospital_id:
        data["hospitals"] = sorted(set(data["hospitals"]) | {usuario.hospital_id})
    data["role_id"] = usuario.rol_id
    data["role_name"] = usuario.rol.nombre if usuario.rol else ""
    data["username"] = usuario.username
    data["nombre_completo"] = " ".join(filter(None, [usuario.nombre, usuario.apellido])) or usuario.nombre
    return data


def _ensure_personal_role(usuario: Usuario) -> Rol:
    if not usuario.rol:
        raise ValueError("El usuario no tiene un rol asignado")
    role = usuario.rol
    if len(role.usuarios) <= 1:
        return role

    base_name = f"{usuario.username}_personal"
    candidate = base_name
    suffix = 1
    while Rol.query.filter(Rol.nombre == candidate).first():
        suffix += 1
        candidate = f"{base_name}_{suffix}"

    new_role = Rol(nombre=candidate, descripcion=f"Permisos personalizados de {usuario.nombre}")
    db.session.add(new_role)
    db.session.flush()

    for permiso in role.permisos:
        db.session.add(
            Permiso(
                rol=new_role,
                modulo=permiso.modulo,
                hospital_id=permiso.hospital_id,
                can_read=permiso.can_read,
                can_write=permiso.can_write,
                allow_export=permiso.allow_export,
            )
        )

    usuario.rol = new_role
    db.session.flush()
    return new_role


@permisos_bp.route("/")
@login_required
@permissions_required("auditoria:read")
def listar():
    usuarios = Usuario.query.order_by(Usuario.nombre.asc()).all()
    if not usuarios:
        page_data = {
            "usuarios": [],
            "hospitales": [],
            "modulos": [],
            "selected_user_id": None,
            "user_states": {},
            "role_templates": [],
            "role_payloads": {},
            "save_url_template": url_for("permisos.guardar_usuario", usuario_id=0),
        }
        return render_template("permisos/listar.html", page_data=page_data)

    selected_id = request.args.get("usuario_id", type=int)
    selected_usuario = next((u for u in usuarios if u.id == selected_id), usuarios[0])

    hospitales = Hospital.query.order_by(Hospital.nombre.asc()).all()
    hospital_options = [
        {"id": 0, "nombre": "Todos los hospitales"},
        *[{"id": hospital.id, "nombre": hospital.nombre} for hospital in hospitales],
    ]

    modulos = [
        {"value": modulo.value, "label": _format_module_label(modulo)}
        for modulo in Modulo
    ]

    roles = Rol.query.order_by(Rol.nombre.asc()).all()
    role_templates = [
        {"id": rol.id, "label": rol.nombre.title()}
        for rol in roles
    ]
    role_payloads = {str(rol.id): _serialize_permissions(rol.permisos) for rol in roles}

    user_states = {str(usuario.id): _serialize_usuario(usuario) for usuario in usuarios}

    page_data = {
        "usuarios": [
            {"id": usuario.id, "label": f"{usuario.nombre} ({usuario.username})"}
            for usuario in usuarios
        ],
        "hospitales": hospital_options,
        "modulos": modulos,
        "selected_user_id": selected_usuario.id,
        "user_states": user_states,
        "role_templates": role_templates,
        "role_payloads": role_payloads,
        "save_url_template": url_for("permisos.guardar_usuario", usuario_id=0),
    }

    return render_template("permisos/listar.html", page_data=page_data)


@permisos_bp.route("/usuarios/<int:usuario_id>/guardar", methods=["POST"])
@login_required
@permissions_required("auditoria:write")
def guardar_usuario(usuario_id: int):
    if not _require_superadmin():
        return jsonify({"error": "No tiene permisos para modificar"}), 403

    usuario = Usuario.query.get_or_404(usuario_id)
    payload = request.get_json(silent=True) or {}

    raw_hospitals = payload.get("hospitals", [])
    if not isinstance(raw_hospitals, list):
        return jsonify({"error": "Formato de hospitales inválido"}), 400
    try:
        hospital_ids = {int(h) for h in raw_hospitals}
    except (TypeError, ValueError):
        return jsonify({"error": "Identificador de hospital inválido"}), 400
    if not hospital_ids:
        return jsonify({"error": "Seleccione al menos un hospital"}), 400

    valid_ids = {hid for hid in hospital_ids if hid != 0}
    if valid_ids:
        existentes = {
            hospital.id
            for hospital in Hospital.query.filter(Hospital.id.in_(valid_ids)).all()
        }
        faltantes = valid_ids - existentes
        if faltantes:
            return jsonify({"error": "Hospital seleccionado no existe"}), 400

    modules_payload: dict[Modulo, dict[str, bool]] = {}
    raw_modules = payload.get("modules", {})
    if not isinstance(raw_modules, dict):
        return jsonify({"error": "Formato de módulos inválido"}), 400
    for modulo in Modulo:
        module_entry = raw_modules.get(modulo.value, {})
        if not isinstance(module_entry, dict):
            module_entry = {}
        modules_payload[modulo] = {
            "can_read": bool(module_entry.get("can_read")),
            "can_write": bool(module_entry.get("can_write")),
            "allow_export": bool(module_entry.get("allow_export")),
        }

    if all(not any(flags.values()) for flags in modules_payload.values()):
        return jsonify({"error": "Debe habilitar al menos un módulo"}), 400

    role = _ensure_personal_role(usuario)

    db.session.query(Permiso).filter(Permiso.rol_id == role.id).delete(synchronize_session=False)

    for modulo, flags in modules_payload.items():
        if not any(flags.values()):
            continue
        for hospital_id in hospital_ids:
            permiso = Permiso(
                rol_id=role.id,
                modulo=modulo,
                hospital_id=None if hospital_id == 0 else hospital_id,
                can_read=flags["can_read"],
                can_write=flags["can_write"],
                allow_export=flags["allow_export"],
            )
            db.session.add(permiso)

    principal = next((hid for hid in hospital_ids if hid != 0), None)
    usuario.hospital_id = principal

    db.session.commit()
    log_action(
        usuario_id=current_user.id,
        accion="configurar",
        modulo="permisos",
        tabla="permisos",
        registro_id=usuario.id,
    )

    return jsonify({"status": "ok", "payload": _serialize_usuario(usuario)})


@permisos_bp.route("/crear", methods=["GET", "POST"])
@login_required
@permissions_required("auditoria:write")
def crear():
    if not _require_superadmin():
        return redirect(url_for("permisos.listar"))
    form = PermisoForm()
    if form.validate_on_submit():
        permiso = Permiso(
            rol_id=form.rol_id.data,
            modulo=Modulo(form.modulo.data),
            hospital_id=form.hospital_id.data or None,
            can_read=form.can_read.data,
            can_write=form.can_write.data,
            allow_export=form.allow_export.data,
        )
        db.session.add(permiso)
        db.session.commit()
        log_action(usuario_id=current_user.id, accion="crear", modulo="permisos", tabla="permisos", registro_id=permiso.id)
        flash("Permiso creado", "success")
        return redirect(url_for("permisos.listar"))
    return render_template("permisos/formulario.html", form=form, titulo="Nuevo permiso")


@permisos_bp.route("/<int:permiso_id>/editar", methods=["GET", "POST"])
@login_required
@permissions_required("auditoria:write")
def editar(permiso_id: int):
    if not _require_superadmin():
        return redirect(url_for("permisos.listar"))
    permiso = Permiso.query.get_or_404(permiso_id)
    form = PermisoForm(obj=permiso)
    if form.validate_on_submit():
        permiso.rol_id = form.rol_id.data
        permiso.modulo = Modulo(form.modulo.data)
        permiso.hospital_id = form.hospital_id.data or None
        permiso.can_read = form.can_read.data
        permiso.can_write = form.can_write.data
        permiso.allow_export = form.allow_export.data
        db.session.commit()
        log_action(usuario_id=current_user.id, accion="editar", modulo="permisos", tabla="permisos", registro_id=permiso.id)
        flash("Permiso actualizado", "success")
        return redirect(url_for("permisos.listar"))
    return render_template("permisos/formulario.html", form=form, titulo="Editar permiso", permiso=permiso)
