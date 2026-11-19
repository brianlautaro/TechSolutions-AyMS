"""HU-18: el administrador consulta y modifica la información de los clientes."""
import re

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user

from models import (
    ACCION_CLIENTE_BAJA, ACCION_CLIENTE_EDICION, ESTADO_EN_CURSO, ESTADO_PENDIENTE,
    ROL_CLIENTE, HistorialCliente, Solicitud, Usuario, db,
)

clientes_admin_bp = Blueprint("clientes_admin", __name__, url_prefix="/admin/clientes")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
TELEFONO_RE = re.compile(r"^[0-9+()\-\s]*$")

# Campos de contacto que se pueden editar y cómo se nombran en pantalla
CAMPOS = {"nombre": "nombre", "apellido": "apellido", "email": "correo", "telefono": "teléfono"}


@clientes_admin_bp.before_request
def solo_admin():
    if not current_user.is_authenticated:
        return redirect(url_for("auth.login"))
    if not current_user.es_admin:
        abort(403)


def _cliente_o_404(cliente_id):
    cliente = db.session.get(Usuario, cliente_id)
    if cliente is None or cliente.rol != ROL_CLIENTE:
        abort(404)
    return cliente


def _solicitudes_abiertas(cliente):
    """Solicitudes pendientes o en curso del cliente."""
    return (
        Solicitud.query
        .filter(
            Solicitud.usuario_id == cliente.id,
            Solicitud.estado.in_([ESTADO_PENDIENTE, ESTADO_EN_CURSO]),
        )
        .count()
    )


def _historial(cliente, limite=5):
    return (
        HistorialCliente.query
        .filter_by(cliente_id=cliente.id)
        .order_by(HistorialCliente.fecha.desc(), HistorialCliente.id.desc())
        .limit(limite)
        .all()
    )


def _render_ficha(cliente, datos=None, errores=None, estado=200):
    if datos is None:
        datos = {campo: getattr(cliente, campo) or "" for campo in CAMPOS}
    historial = _historial(cliente)
    return render_template(
        "admin/cliente_ficha.html",
        cliente=cliente, datos=datos, errores=errores or {},
        abiertas=_solicitudes_abiertas(cliente),
        historial=historial,
        ultima_modificacion=historial[0] if historial else None,
    ), estado


@clientes_admin_bp.route("/")
def lista():
    """Criterio 1: lista los clientes con nombre, correo, plan y estado."""
    clientes = (
        Usuario.query
        .filter_by(rol=ROL_CLIENTE)
        .order_by(Usuario.nombre, Usuario.apellido)
        .all()
    )
    return render_template("admin/clientes_lista.html", clientes=clientes)


@clientes_admin_bp.route("/<int:cliente_id>")
def ficha(cliente_id):
    return _render_ficha(_cliente_o_404(cliente_id))


@clientes_admin_bp.route("/<int:cliente_id>/editar", methods=["POST"])
def editar(cliente_id):
    """Criterio 2: actualiza los datos de contacto y registra la fecha del cambio."""
    cliente = _cliente_o_404(cliente_id)
    datos = {campo: (request.form.get(campo) or "").strip() for campo in CAMPOS}
    datos["email"] = datos["email"].lower()

    errores = {}
    if not datos["nombre"]:
        errores["nombre"] = "El nombre es obligatorio."
    elif len(datos["nombre"]) > 100:
        errores["nombre"] = "El nombre no puede superar los 100 caracteres."
    if len(datos["apellido"]) > 100:
        errores["apellido"] = "El apellido no puede superar los 100 caracteres."
    if not datos["email"]:
        errores["email"] = "El correo es obligatorio."
    elif len(datos["email"]) > 200 or not EMAIL_RE.match(datos["email"]):
        errores["email"] = "Ingresá un correo válido."
    elif Usuario.query.filter(Usuario.email == datos["email"], Usuario.id != cliente.id).first():
        errores["email"] = "Ya existe otra cuenta con ese correo."
    if len(datos["telefono"]) > 30 or not TELEFONO_RE.match(datos["telefono"]):
        errores["telefono"] = "Usá solo números, espacios y los símbolos + ( ) -, hasta 30 caracteres."
    if errores:
        return _render_ficha(cliente, datos, errores, 400)

    cambiados = [c for c in CAMPOS if (getattr(cliente, c) or "") != datos[c]]
    if not cambiados:
        flash("No hay cambios para guardar.", "info")
        return redirect(url_for("clientes_admin.ficha", cliente_id=cliente.id))

    for campo in cambiados:
        setattr(cliente, campo, datos[campo] or None)
    db.session.add(HistorialCliente(
        cliente=cliente, admin=current_user, accion=ACCION_CLIENTE_EDICION,
        detalle="Datos modificados: " + ", ".join(CAMPOS[c] for c in cambiados),
    ))
    db.session.commit()
    flash("Los datos del cliente se actualizaron.", "success")
    return redirect(url_for("clientes_admin.ficha", cliente_id=cliente.id))


@clientes_admin_bp.route("/<int:cliente_id>/baja", methods=["GET", "POST"])
def baja(cliente_id):
    """Criterios 3 y 4: da de baja al cliente. Si tiene solicitudes abiertas, advierte
    cuántas son y exige una confirmación explícita.

    La sesión se cierra sola: el user_loader de app.py descarta a las cuentas inactivas
    en la siguiente petición, y el login rechaza a las cuentas dadas de baja."""
    cliente = _cliente_o_404(cliente_id)
    if not cliente.activo:
        flash("Ese cliente ya está dado de baja.", "info")
        return redirect(url_for("clientes_admin.ficha", cliente_id=cliente.id))

    abiertas = _solicitudes_abiertas(cliente)
    if request.method == "GET":
        return render_template("admin/cliente_baja.html", cliente=cliente,
                               abiertas=abiertas, error=None)

    if abiertas and not request.form.get("entiendo"):
        error = "Marcá la casilla para confirmar la baja con solicitudes abiertas."
        return render_template("admin/cliente_baja.html", cliente=cliente,
                               abiertas=abiertas, error=error), 400

    cliente.activo = False
    detalle = "Baja de la cuenta"
    if abiertas:
        detalle += f" con {abiertas} solicitud{'es' if abiertas != 1 else ''} abierta{'s' if abiertas != 1 else ''}"
    db.session.add(HistorialCliente(
        cliente=cliente, admin=current_user, accion=ACCION_CLIENTE_BAJA, detalle=detalle,
    ))
    db.session.commit()
    flash(f"{cliente.nombre} fue dado de baja y ya no puede ingresar.", "success")
    return redirect(url_for("clientes_admin.lista"))
