import os
import uuid

from flask import (
    Blueprint, abort, current_app, flash, redirect, render_template,
    request, send_from_directory, url_for,
)
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from models import (
    ESTADOS_CON_CARGA, EXTENSIONES_ADJUNTO, MAX_ADJUNTOS, MAX_BYTES_ADJUNTO,
    Adjunto, Solicitud, db,
)

adjuntos_bp = Blueprint("adjuntos", __name__, url_prefix="/adjuntos")


@adjuntos_bp.before_request
@login_required
def solo_clientes():
    if current_user.es_admin:
        abort(403)


def _carpeta(solicitud_id):
    """Carpeta del disco donde se guardan los archivos de una solicitud."""
    return os.path.join(current_app.root_path, "uploads", f"solicitud_{solicitud_id}")


def _extension(nombre):
    return nombre.rsplit(".", 1)[-1].lower() if "." in nombre else ""


def _tamano(archivo):
    archivo.stream.seek(0, os.SEEK_END)
    tamano = archivo.stream.tell()
    archivo.stream.seek(0)
    return tamano


def _validar(archivo, solicitud):
    """Devuelve el mensaje de error, o None si el archivo es válido."""
    if not archivo or not archivo.filename:
        return "Elegí un archivo para subir."
    if len(solicitud.adjuntos) >= MAX_ADJUNTOS:
        return f"La solicitud ya tiene {MAX_ADJUNTOS} archivos: es el máximo permitido."
    if _extension(archivo.filename) not in EXTENSIONES_ADJUNTO:
        return "Solo se aceptan archivos PDF, JPG o PNG."
    if _tamano(archivo) > MAX_BYTES_ADJUNTO:
        return "El archivo supera el máximo de 5 MB."
    return None


@adjuntos_bp.route("/solicitud/<int:solicitud_id>", methods=["GET", "POST"])
def ver(solicitud_id):
    solicitud = db.get_or_404(Solicitud, solicitud_id)
    if solicitud.usuario_id != current_user.id:
        abort(404)  # no se revela si existe una solicitud de otro cliente

    puede_subir = solicitud.estado in ESTADOS_CON_CARGA

    if request.method == "POST":
        if not puede_subir:
            flash("Esta solicitud ya no admite documentación nueva.", "error")
            return redirect(url_for(".ver", solicitud_id=solicitud.id))

        archivo = request.files.get("archivo")
        error = _validar(archivo, solicitud)
        if error:
            flash(error, "error")
        else:
            extension = _extension(archivo.filename)
            nombre_original = secure_filename(archivo.filename) or f"archivo.{extension}"
            nombre_guardado = f"{uuid.uuid4().hex}.{extension}"

            os.makedirs(_carpeta(solicitud.id), exist_ok=True)
            archivo.save(os.path.join(_carpeta(solicitud.id), nombre_guardado))

            db.session.add(Adjunto(
                solicitud=solicitud,
                nombre_original=nombre_original,
                nombre_guardado=nombre_guardado,
                tamano_bytes=_tamano(archivo),
            ))
            db.session.commit()
            flash("Archivo adjuntado correctamente.", "success")
        return redirect(url_for(".ver", solicitud_id=solicitud.id))

    adjuntos = sorted(solicitud.adjuntos, key=lambda a: a.fecha_carga)
    return render_template(
        "adjuntos/ver.html",
        solicitud=solicitud,
        adjuntos=adjuntos,
        puede_subir=puede_subir,
        maximo=MAX_ADJUNTOS,
        lleno=len(adjuntos) >= MAX_ADJUNTOS,
    )


@adjuntos_bp.route("/<int:adjunto_id>/descargar")
def descargar(adjunto_id):
    adjunto = db.get_or_404(Adjunto, adjunto_id)
    if adjunto.solicitud.usuario_id != current_user.id:
        abort(404)
    return send_from_directory(
        _carpeta(adjunto.solicitud_id),
        adjunto.nombre_guardado,
        download_name=adjunto.nombre_original,
        as_attachment=True,
    )