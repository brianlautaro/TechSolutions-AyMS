"""HU-17: el administrador revisa y responde los reclamos de los clientes."""
from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user

from models import (
    CANAL_EMAIL, EVENTO_RECLAMO_EN_REVISION, EVENTO_RECLAMO_RESPONDIDO,
    MAX_RESPUESTA_RECLAMO, RECLAMO_EN_REVISION, RECLAMO_PENDIENTE, RECLAMO_RESPONDIDO,
    Notificacion, Reclamo, RespuestaReclamo, db,
)

reclamos_admin_bp = Blueprint("reclamos_admin", __name__, url_prefix="/admin/reclamos")


@reclamos_admin_bp.before_request
def solo_admin():
    if not current_user.is_authenticated:
        return redirect(url_for("auth.login"))
    if not current_user.es_admin:
        abort(403)


def _notificar_cliente(reclamo, evento, mensaje):
    """Avisa al cliente (simula NotiSys, igual que HU-08 y HU-16)."""
    db.session.add(Notificacion(
        destinatario=reclamo.usuario,
        cliente=reclamo.usuario,
        reclamo=reclamo,
        solicitud=reclamo.solicitud,
        tipo_evento=evento,
        mensaje=mensaje[:300],
        canal=CANAL_EMAIL,
    ))
    current_app.logger.info("[NotiSys] %s -> %s: %s", CANAL_EMAIL, reclamo.usuario.email, mensaje)


def _reclamo_o_404(reclamo_id):
    return db.get_or_404(Reclamo, reclamo_id)


@reclamos_admin_bp.route("/")
def bandeja():
    """Criterio 1: lista los pendientes y los en revisión (los respondidos, aparte)."""
    ver_respondidos = request.args.get("ver") == "respondidos"
    estados = [RECLAMO_RESPONDIDO] if ver_respondidos else [RECLAMO_PENDIENTE, RECLAMO_EN_REVISION]
    reclamos = (
        Reclamo.query
        .filter(Reclamo.estado.in_(estados))
        .order_by(Reclamo.fecha_ingreso.asc())
        .all()
    )
    return render_template("admin/reclamos_bandeja.html", reclamos=reclamos,
                           ver_respondidos=ver_respondidos)


@reclamos_admin_bp.route("/<int:reclamo_id>")
def detalle(reclamo_id):
    """Criterio 5: si ya está respondido, la plantilla lo muestra en modo lectura."""
    reclamo = _reclamo_o_404(reclamo_id)
    return render_template("admin/reclamo_detalle.html", reclamo=reclamo,
                           max_respuesta=MAX_RESPUESTA_RECLAMO, error=None, texto="")


@reclamos_admin_bp.route("/<int:reclamo_id>/en-revision", methods=["POST"])
def en_revision(reclamo_id):
    """Criterio 2: guarda el estado y notifica al cliente."""
    reclamo = _reclamo_o_404(reclamo_id)
    if reclamo.estado != RECLAMO_PENDIENTE:
        flash("Solo se puede pasar a revisión un reclamo pendiente.", "error")
        return redirect(url_for("reclamos_admin.detalle", reclamo_id=reclamo.id))

    reclamo.estado = RECLAMO_EN_REVISION
    _notificar_cliente(
        reclamo, EVENTO_RECLAMO_EN_REVISION,
        f"Tu reclamo #{reclamo.id} está en revisión. Te vamos a responder a la brevedad.",
    )
    db.session.commit()
    flash(f"El reclamo #{reclamo.id} pasó a revisión y se notificó al cliente.", "success")
    return redirect(url_for("reclamos_admin.detalle", reclamo_id=reclamo.id))


@reclamos_admin_bp.route("/<int:reclamo_id>/responder", methods=["POST"])
def responder(reclamo_id):
    """Criterios 3 y 4: confirma la respuesta (no puede ir vacía), registra la fecha y notifica."""
    reclamo = _reclamo_o_404(reclamo_id)
    if reclamo.estado == RECLAMO_RESPONDIDO:
        flash("Ese reclamo ya fue respondido.", "error")
        return redirect(url_for("reclamos_admin.detalle", reclamo_id=reclamo.id))

    texto = (request.form.get("respuesta") or "").strip()
    error = None
    if not texto:
        error = "Escribí la respuesta antes de enviarla."
    elif len(texto) > MAX_RESPUESTA_RECLAMO:
        error = f"La respuesta no puede superar los {MAX_RESPUESTA_RECLAMO} caracteres."
    if error:
        return render_template("admin/reclamo_detalle.html", reclamo=reclamo,
                               max_respuesta=MAX_RESPUESTA_RECLAMO, error=error, texto=texto), 400

    db.session.add(RespuestaReclamo(reclamo=reclamo, admin=current_user, texto=texto))
    reclamo.estado = RECLAMO_RESPONDIDO
    _notificar_cliente(
        reclamo, EVENTO_RECLAMO_RESPONDIDO,
        f"Respondimos tu reclamo #{reclamo.id}: {texto}",
    )
    db.session.commit()
    flash(f"El reclamo #{reclamo.id} fue respondido y se notificó al cliente.", "success")
    return redirect(url_for("reclamos_admin.detalle", reclamo_id=reclamo.id))
