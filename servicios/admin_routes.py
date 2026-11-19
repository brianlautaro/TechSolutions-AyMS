"""HU-20 / CU-13: el administrador crea, modifica y da de baja servicios del catálogo."""
from datetime import datetime

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user

from models import Reclamo, Servicio, ServicioContratado, Solicitud, db

servicios_admin_bp = Blueprint("servicios_admin", __name__, url_prefix="/admin/servicios")

MAX_NOMBRE = 150
MAX_CATEGORIA = 100
MAX_DESCRIPCION = 500


@servicios_admin_bp.before_request
def solo_admin():
    if not current_user.is_authenticated:
        return redirect(url_for("auth.login"))
    if not current_user.es_admin:
        abort(403)


def _categorias_existentes():
    """Para sugerir en el formulario las categorías que ya se usan."""
    filas = (
        db.session.query(Servicio.categoria)
        .filter(Servicio.categoria.isnot(None))
        .distinct()
        .order_by(Servicio.categoria)
        .all()
    )
    return [f[0] for f in filas]


def _leer_formulario():
    """Devuelve (datos, errores). Nombre, categoría y descripción son obligatorios."""
    datos = {
        "nombre": request.form.get("nombre", "").strip(),
        "categoria": request.form.get("categoria", "").strip(),
        "descripcion": request.form.get("descripcion", "").strip(),
    }
    errores = {}
    if not datos["nombre"]:
        errores["nombre"] = "Indicá el nombre del servicio."
    elif len(datos["nombre"]) > MAX_NOMBRE:
        errores["nombre"] = f"El nombre no puede superar los {MAX_NOMBRE} caracteres."
    if not datos["categoria"]:
        errores["categoria"] = "Indicá la categoría."
    elif len(datos["categoria"]) > MAX_CATEGORIA:
        errores["categoria"] = f"La categoría no puede superar los {MAX_CATEGORIA} caracteres."
    if not datos["descripcion"]:
        errores["descripcion"] = "Escribí una descripción."
    elif len(datos["descripcion"]) > MAX_DESCRIPCION:
        errores["descripcion"] = f"La descripción no puede superar los {MAX_DESCRIPCION} caracteres."
    return datos, errores


def _nombre_repetido(nombre, excluir_id=None):
    consulta = Servicio.query.filter(db.func.lower(Servicio.nombre) == nombre.lower())
    if excluir_id:
        consulta = consulta.filter(Servicio.id != excluir_id)
    return consulta.first() is not None


def _registrar_cambio(servicio):
    """Criterio 2: guarda quién y cuándo modificó el servicio."""
    servicio.modificado_por = current_user
    servicio.fecha_modificacion = datetime.utcnow()


def _render_lista(propuesta=None, status=200):
    servicios = Servicio.query.order_by(Servicio.activo.desc(), Servicio.nombre).all()
    return render_template(
        "admin/servicios.html",
        servicios=servicios,
        propuesta=propuesta,
    ), status


@servicios_admin_bp.route("/")
def listar():
    return _render_lista()


@servicios_admin_bp.route("/nuevo", methods=["GET", "POST"])
def nuevo():
    datos = {"nombre": "", "categoria": "", "descripcion": ""}
    errores = {}

    if request.method == "POST":
        datos, errores = _leer_formulario()
        if not errores and _nombre_repetido(datos["nombre"]):
            errores["nombre"] = "Ya existe un servicio con ese nombre."
        if not errores:
            # Criterio 1: queda registrado como disponible
            servicio = Servicio(activo=True, **datos)
            _registrar_cambio(servicio)
            db.session.add(servicio)
            db.session.commit()
            flash(f"Servicio «{servicio.nombre}» creado y disponible en el catálogo.", "success")
            return redirect(url_for(".listar"))

    return render_template(
        "admin/servicio_form.html",
        servicio=None,
        datos=datos,
        errores=errores,
        categorias=_categorias_existentes(),
    ), (400 if errores else 200)


@servicios_admin_bp.route("/<int:servicio_id>/editar", methods=["GET", "POST"])
def editar(servicio_id):
    servicio = db.get_or_404(Servicio, servicio_id)
    datos = {
        "nombre": servicio.nombre,
        "categoria": servicio.categoria or "",
        "descripcion": servicio.descripcion or "",
    }
    errores = {}

    if request.method == "POST":
        datos, errores = _leer_formulario()
        if not errores and _nombre_repetido(datos["nombre"], excluir_id=servicio.id):
            errores["nombre"] = "Ya existe otro servicio con ese nombre."
        if not errores:
            servicio.nombre = datos["nombre"]
            servicio.categoria = datos["categoria"]
            servicio.descripcion = datos["descripcion"]
            _registrar_cambio(servicio)  # criterio 2
            db.session.commit()
            flash(f"Cambios guardados en «{servicio.nombre}».", "success")
            return redirect(url_for(".listar"))

    return render_template(
        "admin/servicio_form.html",
        servicio=servicio,
        datos=datos,
        errores=errores,
        categorias=_categorias_existentes(),
    ), (400 if errores else 200)


@servicios_admin_bp.route("/<int:servicio_id>/eliminar", methods=["POST"])
def eliminar(servicio_id):
    servicio = db.get_or_404(Servicio, servicio_id)

    # Criterio 3: con solicitudes asociadas no se elimina; se propone desactivarlo.
    # También se cuentan contrataciones y reclamos: borrarlo dejaría esos registros sin servicio.
    solicitudes = Solicitud.query.filter_by(servicio_id=servicio.id).count()
    contrataciones = ServicioContratado.query.filter_by(servicio_id=servicio.id).count()
    reclamos = Reclamo.query.filter_by(servicio_id=servicio.id).count()

    if solicitudes or contrataciones or reclamos:
        return _render_lista(
            propuesta={
                "servicio": servicio,
                "solicitudes": solicitudes,
                "contrataciones": contrataciones,
                "reclamos": reclamos,
            },
            status=409,
        )

    nombre = servicio.nombre
    db.session.delete(servicio)
    db.session.commit()
    flash(f"Servicio «{nombre}» eliminado.", "success")
    return redirect(url_for(".listar"))


@servicios_admin_bp.route("/<int:servicio_id>/desactivar", methods=["POST"])
def desactivar(servicio_id):
    """Criterio 4: deja de ofrecerse en el catálogo y no se pueden abrir solicitudes nuevas.

    No hace falta tocar nada más: el catálogo (HU-05) muestra solo servicios activos y
    Usuario.servicios_activos (HU-06 / HU-08) ya filtra por servicio.activo.
    """
    servicio = db.get_or_404(Servicio, servicio_id)
    if not servicio.activo:
        flash(f"«{servicio.nombre}» ya estaba desactivado.", "error")
    else:
        servicio.activo = False
        _registrar_cambio(servicio)
        db.session.commit()
        flash(
            f"«{servicio.nombre}» desactivado: ya no se ofrece en el catálogo y "
            "sus clientes no pueden abrir solicitudes nuevas sobre él.",
            "success",
        )
    return redirect(url_for(".listar"))


@servicios_admin_bp.route("/<int:servicio_id>/activar", methods=["POST"])
def activar(servicio_id):
    servicio = db.get_or_404(Servicio, servicio_id)
    if servicio.activo:
        flash(f"«{servicio.nombre}» ya estaba activo.", "error")
    else:
        servicio.activo = True
        _registrar_cambio(servicio)
        db.session.commit()
        flash(f"«{servicio.nombre}» vuelve a estar disponible en el catálogo.", "success")
    return redirect(url_for(".listar"))
