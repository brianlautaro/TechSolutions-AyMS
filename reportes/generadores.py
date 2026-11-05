"""HU-24: arma los datos de cada reporte como (columnas, filas).

La misma lista de filas se usa para la tabla en pantalla, el CSV y el PDF.
"""
from datetime import timedelta

from models import ROL_CLIENTE, Plan, Solicitud, Usuario

FORMATO_FECHA = "%d/%m/%Y %H:%M"


def _en_rango(consulta, columna, desde, hasta):
    """Filtra por fecha incluyendo el día 'hasta' completo."""
    return consulta.filter(columna >= desde, columna < hasta + timedelta(days=1))


def _fecha(valor):
    return valor.strftime(FORMATO_FECHA) if valor else "-"


def reporte_solicitudes(desde, hasta):
    solicitudes = (
        _en_rango(Solicitud.query, Solicitud.fecha_ingreso, desde, hasta)
        .order_by(Solicitud.fecha_ingreso)
        .all()
    )
    columnas = ["#", "Ingreso", "Cliente", "Plan", "Servicio", "Tipo",
                "Prioridad", "Estado", "Resolución"]
    filas = [
        [
            s.id,
            _fecha(s.fecha_ingreso),
            f"{s.usuario.nombre} {s.usuario.apellido or ''}".strip(),
            s.usuario.plan.nombre if s.usuario.plan else "-",
            s.servicio.nombre,
            s.tipo_modificacion,
            s.prioridad or "-",
            s.estado,
            _fecha(s.fecha_resolucion),
        ]
        for s in solicitudes
    ]
    return columnas, filas


def reporte_planes(desde, hasta):
    columnas = ["Plan", "Respuesta (h)", "Clientes activos",
                "Altas en el período", "Solicitudes en el período"]
    filas = []
    for plan in Plan.query.order_by(Plan.tiempo_respuesta_horas).all():
        clientes = Usuario.query.filter_by(rol=ROL_CLIENTE, plan_id=plan.id)
        activos = clientes.filter_by(activo=True).count()
        altas = _en_rango(clientes, Usuario.fecha_alta, desde, hasta).count()
        solicitudes = _en_rango(
            Solicitud.query.join(Solicitud.usuario).filter(Usuario.plan_id == plan.id),
            Solicitud.fecha_ingreso, desde, hasta,
        ).count()
        filas.append([plan.nombre, plan.tiempo_respuesta_horas, activos, altas, solicitudes])

    # Si en el período no hubo ni altas ni solicitudes, no hay datos para ese rango
    if not any(fila[3] or fila[4] for fila in filas):
        return columnas, []
    return columnas, filas


# Tipos de reporte disponibles. Para sumar uno nuevo, se agrega acá.
REPORTES = {
    "planes": {"titulo": "Planes", "generar": reporte_planes},
    "solicitudes": {"titulo": "Solicitudes", "generar": reporte_solicitudes},
    # "reclamos":  cuando exista el modelo de HU-16
    # "actividad": cuando exista el modelo de HU-23
}