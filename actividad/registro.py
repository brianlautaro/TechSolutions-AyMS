"""HU-23: registra la actividad de los clientes (inicio de sesión, solicitud, adjunto, reclamo)."""
from datetime import datetime

from flask_login import user_logged_in
from sqlalchemy import event, select

from models import (
    ACCION_ADJUNTO,
    ACCION_INICIO_SESION,
    ACCION_RECLAMO,
    ACCION_SOLICITUD,
    ROL_CLIENTE,
    ActividadCliente,
    Adjunto,
    Reclamo,
    Solicitud,
    db,
)


def _anotar(connection, usuario_id, tipo_accion, detalle):
    connection.execute(
        ActividadCliente.__table__.insert().values(
            usuario_id=usuario_id,
            tipo_accion=tipo_accion,
            detalle=detalle[:200],
            fecha=datetime.utcnow(),
        )
    )


def _al_iniciar_sesion(sender, user, **extra):
    if user.rol != ROL_CLIENTE:
        return
    db.session.add(
        ActividadCliente(
            usuario_id=user.id,
            tipo_accion=ACCION_INICIO_SESION,
            detalle="Inicio de sesión",
        )
    )
    db.session.commit()


def _solicitud_creada(mapper, connection, solicitud):
    _anotar(connection, solicitud.usuario_id, ACCION_SOLICITUD, f"Solicitud N° {solicitud.id}")


def _reclamo_creado(mapper, connection, reclamo):
    _anotar(connection, reclamo.usuario_id, ACCION_RECLAMO, f"Reclamo N° {reclamo.id}")


def _adjunto_creado(mapper, connection, adjunto):
    tabla = Solicitud.__table__
    usuario_id = connection.execute(
        select(tabla.c.usuario_id).where(tabla.c.id == adjunto.solicitud_id)
    ).scalar()
    if usuario_id is not None:
        _anotar(
            connection,
            usuario_id,
            ACCION_ADJUNTO,
            f"{adjunto.nombre_original} (solicitud N° {adjunto.solicitud_id})",
        )


def _bloquear_cambios(mapper, connection, actividad):
    raise RuntimeError("Los registros de actividad no se pueden modificar ni eliminar.")


def iniciar_registro_actividad():
    """Se llama una sola vez desde app.py para activar todos los 'escuchas'."""
    user_logged_in.connect(_al_iniciar_sesion)
    event.listen(Solicitud, "after_insert", _solicitud_creada)
    event.listen(Reclamo, "after_insert", _reclamo_creado)
    event.listen(Adjunto, "after_insert", _adjunto_creado)
    event.listen(ActividadCliente, "before_update", _bloquear_cambios)
    event.listen(ActividadCliente, "before_delete", _bloquear_cambios)