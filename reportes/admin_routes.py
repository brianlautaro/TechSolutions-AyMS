"""HU-24: sección de reportes (pantalla + descargas)."""
import csv
import io
from datetime import datetime

from flask import Blueprint, Response, abort, redirect, render_template, request, url_for
from flask_login import current_user

from reportes.generadores import REPORTES

reportes_admin_bp = Blueprint("reportes_admin", __name__, url_prefix="/admin/reportes")


@reportes_admin_bp.before_request
def solo_admin():
    if not current_user.is_authenticated:
        return redirect(url_for("auth.login"))
    if not current_user.es_admin:
        abort(403)


def _leer_parametros(args):
    """Valida tipo y fechas. Devuelve (tipo, desde, hasta, error)."""
    tipo = args.get("tipo", "")
    if tipo not in REPORTES:
        return None, None, None, "Elegí un tipo de reporte."
    try:
        desde = datetime.strptime(args.get("desde", ""), "%Y-%m-%d")
        hasta = datetime.strptime(args.get("hasta", ""), "%Y-%m-%d")
    except ValueError:
        return None, None, None, "Indicá la fecha de inicio y la de fin."
    if desde > hasta:
        return None, None, None, "La fecha de inicio no puede ser posterior a la de fin."
    return tipo, desde, hasta, None


@reportes_admin_bp.route("/")
def generar():
    contexto = {
        "reportes": REPORTES,
        "filtros": request.args,
        "error": None,
        "columnas": None,
        "filas": None,
    }
    # Primera vez que se entra (sin parámetros): solo el formulario
    if not request.args:
        return render_template("admin/reportes.html", **contexto)

    tipo, desde, hasta, error = _leer_parametros(request.args)
    if error:
        contexto["error"] = error
        return render_template("admin/reportes.html", **contexto)

    columnas, filas = REPORTES[tipo]["generar"](desde, hasta)
    contexto.update(columnas=columnas, filas=filas, titulo=REPORTES[tipo]["titulo"])
    return render_template("admin/reportes.html", **contexto)


@reportes_admin_bp.route("/descargar/<formato>")
def descargar(formato):
    tipo, desde, hasta, error = _leer_parametros(request.args)
    if error:
        abort(400)
    columnas, filas = REPORTES[tipo]["generar"](desde, hasta)
    nombre = f"reporte_{tipo}_{desde:%Y%m%d}_{hasta:%Y%m%d}"

    if formato == "csv":
        return _respuesta_csv(nombre, columnas, filas)
    # Paso 3: acá se agrega el PDF
    abort(404)


def _respuesta_csv(nombre, columnas, filas):
    salida = io.StringIO()
    # ";" porque Excel en español usa la coma como separador decimal
    escritor = csv.writer(salida, delimiter=";")
    escritor.writerow(columnas)
    escritor.writerows(filas)
    # "utf-8-sig" agrega una marca al inicio para que Excel muestre bien los acentos
    contenido = salida.getvalue().encode("utf-8-sig")
    return Response(
        contenido,
        mimetype="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{nombre}.csv"'},
    )