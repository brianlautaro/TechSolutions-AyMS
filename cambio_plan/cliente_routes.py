"""HU-07: el cliente ve los planes y pide el cambio a otro."""
from flask import Blueprint, abort, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from models import MAX_MOTIVO_CAMBIO_PLAN, SolicitudCambioPlan, db

from cambio_plan.logica import CambioPlanError, planes_para_elegir, registrar_cambio_plan

cambio_plan_cliente_bp = Blueprint("cambio_plan", __name__, url_prefix="/mi-plan")


@cambio_plan_cliente_bp.before_request
@login_required
def solo_clientes():
    # El cambio lo pide el cliente; el admin lo resuelve desde su panel
    if current_user.es_admin:
        abort(403)


def _pantalla_planes(error=None, pendiente=None, datos=None, status=200):
    return render_template(
        "cambio_plan/planes.html",
        planes=planes_para_elegir(current_user),
        pendiente=pendiente or SolicitudCambioPlan.pendiente_de(current_user),
        error=error,
        datos=datos or {},
        max_motivo=MAX_MOTIVO_CAMBIO_PLAN,
    ), status


# Criterio 1: muestra los planes disponibles y marca el contratado
@cambio_plan_cliente_bp.route("/")
def planes():
    return _pantalla_planes()


# Criterios 2, 3 y 4
@cambio_plan_cliente_bp.route("/solicitar", methods=["POST"])
def solicitar():
    datos = {
        "plan_id": request.form.get("plan_id", type=int),
        "motivo": request.form.get("motivo", ""),
    }
    try:
        solicitud = registrar_cambio_plan(current_user, datos["plan_id"], datos["motivo"])
    except CambioPlanError as e:
        return _pantalla_planes(error=e.mensaje, pendiente=e.pendiente, datos=datos, status=400)
    return redirect(url_for(".confirmacion", solicitud_id=solicitud.id))


@cambio_plan_cliente_bp.route("/solicitudes/<int:solicitud_id>")
def confirmacion(solicitud_id):
    solicitud = db.get_or_404(SolicitudCambioPlan, solicitud_id)
    if solicitud.usuario_id != current_user.id:
        abort(404)  # no se revela si existe una solicitud de otro cliente
    return render_template("cambio_plan/confirmacion.html", solicitud=solicitud)