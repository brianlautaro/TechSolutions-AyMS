"""HU-08: el cliente registra una solicitud de modificación sobre un servicio contratado."""
from flask import Blueprint, abort, current_app, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from models import (
    CANAL_EMAIL, ESTADO_PENDIENTE, EVENTO_NUEVA_SOLICITUD, ROL_ADMIN, TIPOS_MODIFICACION,
    Notificacion, Solicitud, Usuario, db,
)

solicitudes_cliente_bp = Blueprint("solicitudes_cliente", __name__, url_prefix="/solicitudes")

MAX_DESCRIPCION = 1000


@solicitudes_cliente_bp.before_request
@login_required
def solo_clientes():
    # Las solicitudes las abre el cliente; el admin las atiende desde su bandeja
    if current_user.es_admin:
        abort(403)


def _notificar_admins(solicitud):
    """Paso 6 del CU-01: avisa al administrador de la nueva solicitud (simula NotiSys)."""
    mensaje = (
        f"Nueva solicitud #{solicitud.id} de {solicitud.usuario.nombre} "
        f"{solicitud.usuario.apellido or ''}: {solicitud.tipo_modificacion} "
        f"en «{solicitud.servicio.nombre}»."
    ).replace("  ", " ")
    admins = Usuario.query.filter_by(rol=ROL_ADMIN, activo=True).all()
    for admin in admins:
        db.session.add(Notificacion(
            destinatario=admin,
            cliente=solicitud.usuario,
            solicitud=solicitud,
            tipo_evento=EVENTO_NUEVA_SOLICITUD,
            mensaje=mensaje,
            canal=CANAL_EMAIL,
        ))
        current_app.logger.info("[NotiSys] %s -> %s: %s", CANAL_EMAIL, admin.email, mensaje)


@solicitudes_cliente_bp.route("/nueva", methods=["GET", "POST"])
def nueva():
    servicios = current_user.servicios_activos
    creditos = current_user.creditos_restantes

    # Lo que eligió el cliente (o el servicio que viene preseleccionado desde "Mis servicios")
    datos = {
        "servicio_id": request.values.get("servicio_id", type=int),
        "tipo_modificacion": request.form.get("tipo_modificacion", ""),
        "descripcion": request.form.get("descripcion", "").strip(),
    }
    errores = {}

    if request.method == "POST" and servicios:
        ids_validos = {c.servicio_id for c in servicios}

        # Criterio 4: sin créditos no hay alta
        if creditos <= 0:
            errores["general"] = (
                "Tu plan no tiene créditos disponibles este mes: el saldo está agotado. "
                "Podés esperar al mes próximo o pedir un cambio de plan."
            )
        # Flujo alternativo 5 del CU-01: el servicio tiene que ser del cliente y estar activo
        if datos["servicio_id"] not in ids_validos:
            errores["servicio_id"] = "Elegí uno de tus servicios activos."
        if datos["tipo_modificacion"] not in TIPOS_MODIFICACION:
            errores["tipo_modificacion"] = "Elegí el tipo de modificación."
        # Criterio 2: la descripción es obligatoria
        if not datos["descripcion"]:
            errores["descripcion"] = "Escribí una descripción de lo que necesitás."
        elif len(datos["descripcion"]) > MAX_DESCRIPCION:
            errores["descripcion"] = f"La descripción no puede superar los {MAX_DESCRIPCION} caracteres."

        if not errores:
            # Criterio 3: queda pendiente, con fecha de ingreso, y se avisa al admin
            solicitud = Solicitud(
                usuario=current_user,
                servicio_id=datos["servicio_id"],
                tipo_modificacion=datos["tipo_modificacion"],
                descripcion=datos["descripcion"],
                estado=ESTADO_PENDIENTE,  # la prioridad la asigna el admin (CU-02 / HU-12)
            )
            db.session.add(solicitud)
            db.session.flush()  # para tener el id antes de armar la notificación
            _notificar_admins(solicitud)
            db.session.commit()
            return redirect(url_for(".confirmacion", solicitud_id=solicitud.id))

    return render_template(
        "solicitudes/nueva.html",
        servicios=servicios,
        tipos=TIPOS_MODIFICACION,
        creditos=creditos,
        datos=datos,
        errores=errores,
        max_descripcion=MAX_DESCRIPCION,
    ), (400 if errores else 200)


@solicitudes_cliente_bp.route("/<int:solicitud_id>/confirmacion")
def confirmacion(solicitud_id):
    solicitud = db.get_or_404(Solicitud, solicitud_id)
    if solicitud.usuario_id != current_user.id:
        abort(404)  # no se revela si existe una solicitud de otro cliente
    return render_template(
        "solicitudes/confirmacion.html",
        solicitud=solicitud,
        creditos=current_user.creditos_restantes,
    )