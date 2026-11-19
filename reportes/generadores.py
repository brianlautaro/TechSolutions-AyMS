"""HU-24: arma los datos de cada reporte como (columnas, filas).

La misma lista de filas se usa para la tabla en pantalla, el CSV y el PDF.
"""
from datetime import timedelta

from actividad.admin_routes import NOMBRE_ACCION
from models import (
    RECLAMO_EN_REVISION, RECLAMO_PENDIENTE, RECLAMO_RESPONDIDO, ROL_CLIENTE,
    ActividadCliente, Plan, Reclamo, Solicitud, Usuario,
)

FORMATO_FECHA = "%d/%m/%Y %H:%M"
NOMBRE_ESTADO_RECLAMO = {
    RECLAMO_PENDIENTE: "Pendiente",
    RECLAMO_EN_REVISION: "En revisión",
    RECLAMO_RESPONDIDO: "Respondido",
}


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

def _recortar(texto, largo=80):
    """Las descripciones pueden ser largas: en el reporte va un resumen."""
    texto = (texto or "").replace("\n", " ").strip()
    return texto if len(texto) <= largo else texto[: largo - 1] + "…"


def reporte_reclamos(desde, hasta):
    reclamos = (
        _en_rango(Reclamo.query, Reclamo.fecha_ingreso, desde, hasta)
        .order_by(Reclamo.fecha_ingreso)
        .all()
    )
    columnas = ["#", "Ingreso", "Cliente", "Servicio", "Solicitud",
                "Estado", "Descripción", "Respondido"]
    filas = [
        [
            r.id,
            _fecha(r.fecha_ingreso),
            f"{r.usuario.nombre} {r.usuario.apellido or ''}".strip(),
            r.servicio.nombre if r.servicio else "-",
            f"#{r.solicitud_id}" if r.solicitud_id else "-",
            NOMBRE_ESTADO_RECLAMO.get(r.estado, r.estado),
            _recortar(r.descripcion),
            _fecha(r.respuesta.fecha) if r.respuesta else "-",
        ]
        for r in reclamos
    ]
    return columnas, filas


def reporte_actividad(desde, hasta):
    registros = (
        _en_rango(ActividadCliente.query, ActividadCliente.fecha, desde, hasta)
        .order_by(ActividadCliente.fecha)
        .all()
    )
    columnas = ["Fecha", "Cliente", "Email", "Acción", "Detalle"]
    filas = [
        [
            _fecha(a.fecha),
            f"{a.usuario.nombre} {a.usuario.apellido or ''}".strip(),
            a.usuario.email,
            NOMBRE_ACCION.get(a.tipo_accion, a.tipo_accion),
            a.detalle or "-",
        ]
        for a in registros
    ]
    return columnas, filas


# Tipos de reporte disponibles. Para sumar uno nuevo, se agrega acá.
REPORTES = {
    "planes": {"titulo": "Planes", "generar": reporte_planes},
    "solicitudes": {"titulo": "Solicitudes", "generar": reporte_solicitudes},
    "reclamos": {"titulo": "Reclamos", "generar": reporte_reclamos},
    "actividad": {"titulo": "Actividad de clientes", "generar": reporte_actividad},
}