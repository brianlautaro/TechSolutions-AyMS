"""HU-05: el cliente consulta el catálogo y contrata un servicio."""
from datetime import datetime

from flask import Blueprint, abort, current_app, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from models import (
    CANAL_EMAIL, EVENTO_NUEVA_CONTRATACION, ROL_ADMIN,
    Notificacion, Servicio, ServicioContratado, Usuario, db,
)

catalogo_bp = Blueprint("catalogo", __name__, url_prefix="/catalogo")


@catalogo_bp.before_request
@login_required
def solo_clientes():
    # El catálogo para contratar es del cliente; el admin gestiona servicios en HU-20
    if current_user.es_admin:
        abort(403)


def _tiene_plan_activo():
    return current_user.plan is not None and current_user.plan.activo


def _ya_contratado(servicio_id):
    return ServicioContratado.query.filter_by(
        usuario_id=current_user.id, servicio_id=servicio_id, activo=True
    ).first() is not None


def _notificar_admins(servicio):
    """Criterio 4: avisa al administrador de la contratación (simula NotiSys)."""
    mensaje = (
        f"{current_user.nombre} {current_user.apellido or ''} "
        f"contrató el servicio «{servicio.nombre}»."
    ).replace("  ", " ")
    for admin in Usuario.query.filter_by(rol=ROL_ADMIN, activo=True).all():
        db.session.add(Notificacion(
            destinatario=admin,
            cliente=current_user,
            tipo_evento=EVENTO_NUEVA_CONTRATACION,
            mensaje=mensaje,
            canal=CANAL_EMAIL,
        ))
        current_app.logger.info("[NotiSys] %s -> %s: %s", CANAL_EMAIL, admin.email, mensaje)


@catalogo_bp.route("/")
def listar():
    # Criterio 3: solo se ofrecen los servicios activos
    servicios = (
        Servicio.query.filter_by(activo=True)
        .order_by(Servicio.categoria, Servicio.nombre)
        .all()
    )
    contratados = {c.servicio_id for c in current_user.servicios_contratados if c.activo}
    return render_template(
        "catalogo.html",
        servicios=servicios,
        contratados=contratados,
        tiene_plan=_tiene_plan_activo(),
    )


@catalogo_bp.route("/<int:servicio_id>/contratar", methods=["POST"])
def contratar(servicio_id):
    servicio = db.get_or_404(Servicio, servicio_id)

    if not servicio.activo:  # criterio 3 (por si alguien arma la dirección a mano)
        flash("Ese servicio no está disponible en el catálogo.", "error")
    elif not _tiene_plan_activo():
        flash("Necesitás un plan activo para contratar servicios.", "error")
    elif _ya_contratado(servicio.id):  # criterio 2
        flash(f"Ya tenés contratado «{servicio.nombre}».", "error")
    else:
        # Criterio 1: queda asociado a tu cuenta, activo y con fecha de contratación
        db.session.add(ServicioContratado(
            usuario=current_user,
            servicio=servicio,
            activo=True,
            fecha_alta=datetime.utcnow(),
        ))
        _notificar_admins(servicio)  # criterio 4
        db.session.commit()
        flash(f"¡Listo! Contrataste «{servicio.nombre}».", "success")

    return redirect(url_for(".listar"))