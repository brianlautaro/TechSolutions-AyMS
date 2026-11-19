"""HU-07: reglas para registrar un cambio de plan.

Están separadas de las rutas para que las use tanto el formulario web como,
en el release posterior, el canal de WhatsApp Business (criterio 5): ese canal
solo tiene que buscar al cliente por su teléfono y llamar a registrar_cambio_plan()
con origen=ORIGEN_WHATSAPP.
"""
from flask import current_app

from models import (
    CANAL_EMAIL, ESTADO_PENDIENTE, EVENTO_CAMBIO_PLAN, MAX_MOTIVO_CAMBIO_PLAN,
    ORIGEN_WEB, ROL_ADMIN, Notificacion, Plan, SolicitudCambioPlan, Usuario, db,
)


class CambioPlanError(Exception):
    """El pedido no se puede registrar. `pendiente` trae la solicitud en curso (criterio 4)."""

    def __init__(self, mensaje, pendiente=None):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.pendiente = pendiente


def planes_para_elegir(cliente):
    """Criterio 1: planes disponibles + el actual del cliente (aunque esté desactivado,
    HU-19 dice que quien lo tiene lo conserva, así que igual se muestra marcado)."""
    planes = Plan.query.filter_by(activo=True).order_by(Plan.tiempo_respuesta_horas.desc()).all()
    if cliente.plan and cliente.plan not in planes:
        planes.insert(0, cliente.plan)
    return planes


def _notificar_admins(solicitud):
    """Paso 3 del CU-09: avisa al administrador (simula NotiSys, igual que HU-08 y HU-16)."""
    cliente = f"{solicitud.usuario.nombre} {solicitud.usuario.apellido or ''}".strip()
    actual = solicitud.plan_actual.nombre if solicitud.plan_actual else "sin plan"
    mensaje = (
        f"Solicitud de cambio de plan #{solicitud.id} de {cliente}: "
        f"{actual} → {solicitud.plan_solicitado.nombre} (vía {solicitud.origen})."
    )
    for admin in Usuario.query.filter_by(rol=ROL_ADMIN, activo=True).all():
        db.session.add(Notificacion(
            destinatario=admin,
            cliente=solicitud.usuario,
            tipo_evento=EVENTO_CAMBIO_PLAN,
            mensaje=mensaje[:300],
            canal=CANAL_EMAIL,
        ))
        current_app.logger.info("[NotiSys] %s -> %s: %s", CANAL_EMAIL, admin.email, mensaje)


def registrar_cambio_plan(cliente, plan_id, motivo="", origen=ORIGEN_WEB):
    """Valida y registra el pedido. Devuelve la SolicitudCambioPlan o lanza CambioPlanError."""
    # Precondición del CU-09: el cliente tiene que tener un plan
    if not cliente.plan:
        raise CambioPlanError("No tenés un plan activo. Contactá a la consultora para contratar uno.")

    # Criterio 4: una sola solicitud de cambio pendiente a la vez
    pendiente = SolicitudCambioPlan.pendiente_de(cliente)
    if pendiente:
        raise CambioPlanError(
            "Ya tenés una solicitud de cambio de plan pendiente. "
            "Esperá a que el administrador la resuelva antes de pedir otra.",
            pendiente=pendiente,
        )

    plan = db.session.get(Plan, plan_id) if plan_id else None
    if not plan:
        raise CambioPlanError("Elegí uno de los planes disponibles.")

    # Criterio 3: el plan elegido es el que ya tiene
    if plan.id == cliente.plan_id:
        raise CambioPlanError(f"«{plan.nombre}» es tu plan vigente. Elegí un plan distinto.")

    # Un plan desactivado ya no se ofrece a clientes (HU-19)
    if not plan.activo:
        raise CambioPlanError(f"El plan «{plan.nombre}» ya no está disponible.")

    motivo = (motivo or "").strip()
    if len(motivo) > MAX_MOTIVO_CAMBIO_PLAN:
        raise CambioPlanError(f"El motivo no puede superar los {MAX_MOTIVO_CAMBIO_PLAN} caracteres.")

    # Criterio 2: queda pendiente y se avisa al admin
    solicitud = SolicitudCambioPlan(
        usuario=cliente,
        plan_actual=cliente.plan,
        plan_solicitado=plan,
        motivo=motivo or None,
        estado=ESTADO_PENDIENTE,
        origen=origen,
    )
    db.session.add(solicitud)
    db.session.flush()  # para tener el id antes de armar la notificación
    _notificar_admins(solicitud)
    db.session.commit()
    return solicitud