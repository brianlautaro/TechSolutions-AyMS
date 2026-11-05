from datetime import datetime, timedelta

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user

from sqlalchemy import case

from models import (
    db, Solicitud, PRIORIDADES, ESTADOS,
    ESTADO_PENDIENTE, ESTADO_EN_CURSO, ESTADO_RECHAZADA, ESTADO_REALIZADO,
    PRIORIDAD_ALTA, PRIORIDAD_MEDIA, PRIORIDAD_BAJA,
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
        

def _parsear_fecha(texto):
    """Convierte 'AAAA-MM-DD' (lo que manda <input type="date">) en datetime, o None."""
    try:
        return datetime.strptime(texto, "%Y-%m-%d")
    except (TypeError, ValueError):
        return None


def consultar_bandeja(args):
    """HU-11: devuelve (solicitudes, filtros) según los parámetros de la URL."""
    filtros = {
        # Sin parámetro 'estado' se muestran las pendientes; estado="" significa "todos"
        "estado": args.get("estado", ESTADO_PENDIENTE),
        "prioridad": args.get("prioridad", ""),
        "desde": args.get("desde", ""),
        "hasta": args.get("hasta", ""),
    }

    consulta = Solicitud.query
    if filtros["estado"] in ESTADOS:
        consulta = consulta.filter(Solicitud.estado == filtros["estado"])
    if filtros["prioridad"] in PRIORIDADES:
        consulta = consulta.filter(Solicitud.prioridad == filtros["prioridad"])

    desde = _parsear_fecha(filtros["desde"])
    hasta = _parsear_fecha(filtros["hasta"])
    if desde:
        consulta = consulta.filter(Solicitud.fecha_ingreso >= desde)
    if hasta:
        # "hasta" incluye todo ese día: menor que el día siguiente a las 00:00
        consulta = consulta.filter(Solicitud.fecha_ingreso < hasta + timedelta(days=1))

    orden_prioridad = case(
        {PRIORIDAD_ALTA: 0, PRIORIDAD_MEDIA: 1, PRIORIDAD_BAJA: 2},
        value=Solicitud.prioridad,
        else_=3,  # sin prioridad, al final
    )
    solicitudes = consulta.order_by(orden_prioridad, Solicitud.fecha_ingreso).all()
    return solicitudes, filtros


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


@solicitudes_admin_bp.route("/<int:solicitud_id>/prioridad", methods=["POST"])
def cambiar_prioridad(solicitud_id):
    solicitud = db.get_or_404(Solicitud, solicitud_id)
    volver = redirect(url_for(".detalle", solicitud_id=solicitud.id))

    if not solicitud.admite_cambio_prioridad:
        flash("No se puede cambiar la prioridad de una solicitud finalizada o rechazada.", "error")
        return volver

    nueva = request.form.get("prioridad", "")
    if nueva not in PRIORIDADES:
        flash("Elegí una prioridad válida: alta, media o baja.", "error")
        return volver

    if nueva == solicitud.prioridad:
        flash("La solicitud ya tenía esa prioridad.", "error")
        return volver

    solicitud.prioridad = nueva
    solicitud.prioridad_modificada_por = current_user
    solicitud.fecha_cambio_prioridad = datetime.utcnow()
    db.session.commit()

    flash(f"Prioridad actualizada a «{nueva}».", "success")
    return volver