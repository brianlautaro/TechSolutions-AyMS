"""HU-16: el cliente presenta un reclamo sobre un inconveniente con los servicios."""
from flask import Blueprint, abort, current_app, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from models import (
    CANAL_EMAIL, EVENTO_NUEVO_RECLAMO, RECLAMO_PENDIENTE, ROL_ADMIN,
    Notificacion, Reclamo, Usuario, db,
)

reclamos_cliente_bp = Blueprint("reclamos_cliente", __name__, url_prefix="/reclamos")

MAX_DESCRIPCION = 1000


@reclamos_cliente_bp.before_request
@login_required
def solo_clientes():
    # Los reclamos los presenta el cliente; el admin los responde en HU-17
    if current_user.es_admin:
        abort(403)


def _opciones_del_cliente():
    """Servicios y solicitudes PROPIOS a los que se puede asociar el reclamo."""
    servicios = sorted(
        {c.servicio for c in current_user.servicios_contratados},
        key=lambda s: s.nombre,
    )
    solicitudes = sorted(current_user.solicitudes, key=lambda s: s.fecha_ingreso, reverse=True)
    return servicios, solicitudes


def _notificar_admins(reclamo):
    """Criterio 3: avisa al administrador del nuevo reclamo (simula NotiSys, igual que HU-08)."""
    cliente = f"{reclamo.usuario.nombre} {reclamo.usuario.apellido or ''}".strip()
    mensaje = f"Nuevo reclamo #{reclamo.id} de {cliente}"
    if reclamo.servicio:
        mensaje += f" sobre «{reclamo.servicio.nombre}»"
    if reclamo.solicitud:
        mensaje += f" (solicitud #{reclamo.solicitud.id})"
    mensaje += "."

    for admin in Usuario.query.filter_by(rol=ROL_ADMIN, activo=True).all():
        db.session.add(Notificacion(
            destinatario=admin,
            cliente=reclamo.usuario,
            reclamo=reclamo,
            solicitud=reclamo.solicitud,
            tipo_evento=EVENTO_NUEVO_RECLAMO,
            mensaje=mensaje[:300],
            canal=CANAL_EMAIL,
        ))
        current_app.logger.info("[NotiSys] %s -> %s: %s", CANAL_EMAIL, admin.email, mensaje)


@reclamos_cliente_bp.route("/nuevo", methods=["GET", "POST"])
def nuevo():
    servicios, solicitudes = _opciones_del_cliente()

    datos = {
        # type=int: si viene vacío o no es un número, queda en None (= sin asociar)
        "servicio_id": request.values.get("servicio_id", type=int),
        "solicitud_id": request.values.get("solicitud_id", type=int),
        "descripcion": request.form.get("descripcion", "").strip(),
    }
    errores = {}

    if request.method == "POST":
        # Criterio 1: asociar es opcional, pero si se elige tiene que ser del propio cliente
        if datos["servicio_id"] and datos["servicio_id"] not in {s.id for s in servicios}:
            errores["servicio_id"] = "Elegí uno de tus servicios o dejalo sin asociar."
        if datos["solicitud_id"] and datos["solicitud_id"] not in {s.id for s in solicitudes}:
            errores["solicitud_id"] = "Elegí una de tus solicitudes o dejala sin asociar."
        # Criterio 2: la descripción es obligatoria
        if not datos["descripcion"]:
            errores["descripcion"] = "Escribí la descripción del reclamo."
        elif len(datos["descripcion"]) > MAX_DESCRIPCION:
            errores["descripcion"] = f"La descripción no puede superar los {MAX_DESCRIPCION} caracteres."

        if not errores:
            # Criterio 3: queda pendiente, con fecha de ingreso, y se avisa al admin
            reclamo = Reclamo(
                usuario=current_user,
                servicio_id=datos["servicio_id"],
                solicitud_id=datos["solicitud_id"],
                descripcion=datos["descripcion"],
                estado=RECLAMO_PENDIENTE,
            )
            db.session.add(reclamo)
            db.session.flush()  # para tener el id antes de armar la notificación
            _notificar_admins(reclamo)
            db.session.commit()
            return redirect(url_for(".confirmacion", reclamo_id=reclamo.id))

    return render_template(
        "reclamos/nuevo.html",
        servicios=servicios,
        solicitudes=solicitudes,
        datos=datos,
        errores=errores,
        max_descripcion=MAX_DESCRIPCION,
    ), (400 if errores else 200)


@reclamos_cliente_bp.route("/<int:reclamo_id>/confirmacion")
def confirmacion(reclamo_id):
    reclamo = db.get_or_404(Reclamo, reclamo_id)
    if reclamo.usuario_id != current_user.id:
        abort(404)  # no se revela si existe un reclamo de otro cliente
    return render_template("reclamos/confirmacion.html", reclamo=reclamo)