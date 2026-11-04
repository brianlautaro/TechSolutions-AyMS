from datetime import datetime

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user

from models import (
    db, Solicitud, PRIORIDADES,
    ESTADO_PENDIENTE, ESTADO_EN_CURSO, ESTADO_RECHAZADA, ESTADO_REALIZADO,
)

solicitudes_admin_bp = Blueprint(
    "solicitudes_admin", __name__, url_prefix="/admin/solicitudes"
)

# Transiciones permitidas: estado actual -> estados a los que puede pasar
TRANSICIONES = {
    ESTADO_PENDIENTE: {ESTADO_EN_CURSO, ESTADO_RECHAZADA},
    ESTADO_EN_CURSO: {ESTADO_REALIZADO},
}


@solicitudes_admin_bp.before_request
def solo_admin():
    if not current_user.is_authenticated:
        return redirect(url_for("auth.login"))
    if not current_user.es_admin:
        abort(403)


def _cambiar_estado(solicitud_id, nuevo, motivo=None):
    solicitud = db.get_or_404(Solicitud, solicitud_id)

    if nuevo not in TRANSICIONES.get(solicitud.estado, set()):
        flash(f"No se puede pasar de «{solicitud.estado}» a «{nuevo}».", "error")
        return redirect(url_for("admin_dashboard"))

    solicitud.estado = nuevo
    if nuevo == ESTADO_RECHAZADA:
        solicitud.motivo_rechazo = motivo
    if nuevo in (ESTADO_RECHAZADA, ESTADO_REALIZADO):
        solicitud.fecha_resolucion = datetime.utcnow()
    db.session.commit()

    flash("Solicitud actualizada.", "success")
    return redirect(url_for("admin_dashboard"))


@solicitudes_admin_bp.route("/<int:solicitud_id>/aprobar", methods=["POST"])
def aprobar(solicitud_id):
    return _cambiar_estado(solicitud_id, ESTADO_EN_CURSO)


@solicitudes_admin_bp.route("/<int:solicitud_id>/rechazar", methods=["POST"])
def rechazar(solicitud_id):
    motivo = request.form.get("motivo", "").strip()
    if not motivo:
        flash("Indicá el motivo del rechazo.", "error")
        return redirect(url_for("admin_dashboard"))
    return _cambiar_estado(solicitud_id, ESTADO_RECHAZADA, motivo[:300])


@solicitudes_admin_bp.route("/<int:solicitud_id>/finalizar", methods=["POST"])
def finalizar(solicitud_id):
    return _cambiar_estado(solicitud_id, ESTADO_REALIZADO)


@solicitudes_admin_bp.route("/<int:solicitud_id>")
def detalle(solicitud_id):
    """HU-12 (y la bandeja de HU-11 enlaza acá): detalle de una solicitud."""
    solicitud = db.get_or_404(Solicitud, solicitud_id)
    return render_template(
        "admin/solicitud_detalle.html",
        solicitud=solicitud,
        prioridades=PRIORIDADES,
    )