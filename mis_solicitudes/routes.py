from datetime import timedelta

from flask import Blueprint, abort, render_template
from flask_login import current_user, login_required

from models import ESTADO_RECHAZADA, ESTADO_REALIZADO, Solicitud

mis_solicitudes_bp = Blueprint("mis_solicitudes", __name__, url_prefix="/mis-solicitudes")


@mis_solicitudes_bp.before_request
@login_required
def solo_clientes():
    if current_user.es_admin:
        abort(403)


@mis_solicitudes_bp.route("/")
def lista():
    solicitudes = (
        Solicitud.query
        .filter_by(usuario_id=current_user.id)
        .order_by(Solicitud.fecha_ingreso.desc())
        .all()
    )

    horas_plan = current_user.plan.tiempo_respuesta_horas if current_user.plan else None

    filas = []
    for s in solicitudes:
        cerrada = s.estado in (ESTADO_REALIZADO, ESTADO_RECHAZADA)
        estimada = None
        if not cerrada and horas_plan and s.fecha_ingreso:
            estimada = s.fecha_ingreso + timedelta(hours=horas_plan)
        filas.append({"solicitud": s, "cerrada": cerrada, "estimada": estimada})

    return render_template("mis_solicitudes/lista.html", filas=filas)