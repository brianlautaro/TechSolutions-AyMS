"""HU-23: el administrador consulta el registro de actividad de los clientes"""
from flask import Blueprint, abort, redirect, render_template, request, url_for
from flask_login import current_user

from models import (
    ACCION_ADJUNTO, ACCION_INICIO_SESION, ACCION_RECLAMO, ACCION_SOLICITUD,
    ActividadCliente,
)

actividad_admin_bp = Blueprint("actividad_admin", __name__, url_prefix="/admin/actividad")

# Cómo se llama cada acción en pantalla
NOMBRE_ACCION = {
    ACCION_INICIO_SESION: "Inicio de sesión",
    ACCION_SOLICITUD: "Solicitud abierta",
    ACCION_ADJUNTO: "Archivo adjuntado",
    ACCION_RECLAMO: "Reclamo presentado",
}


@actividad_admin_bp.before_request
def solo_admin():
    if not current_user.is_authenticated:
        return redirect(url_for("auth.login"))
    if not current_user.es_admin:
        abort(403)


@actividad_admin_bp.route("/")
def lista():
    tipo = request.args.get("tipo", "")
    consulta = ActividadCliente.query
    if tipo in NOMBRE_ACCION:
        consulta = consulta.filter_by(tipo_accion=tipo)
    registros = (
        consulta
        .order_by(ActividadCliente.fecha.desc(), ActividadCliente.id.desc())
        .limit(200)
        .all()
    )
    return render_template(
        "admin/actividad.html",
        registros=registros, nombres=NOMBRE_ACCION, tipo=tipo,
    )