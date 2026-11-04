"""HU-21: emitir y revocar tokens de API para sistemas externos."""
from datetime import datetime
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user

from models import TokenAPI, db

integraciones_admin_bp = Blueprint(
    "integraciones_admin", __name__, url_prefix="/admin/integraciones"
)

# Vigencias que puede elegir el administrador (en días). Se usan en el paso 3.
VIGENCIAS = [30, 90, 180, 365]


@integraciones_admin_bp.before_request
def solo_admin():
    if not current_user.is_authenticated:
        return redirect(url_for("auth.login"))
    if not current_user.es_admin:
        abort(403)


def _render_lista(token_nuevo=None, sistema_nuevo=None):
    tokens = TokenAPI.query.order_by(TokenAPI.fecha_emision.desc()).all()
    return render_template(
        "admin/integraciones.html",
        tokens=tokens,
        vigencias=VIGENCIAS,
        token_nuevo=token_nuevo,
        sistema_nuevo=sistema_nuevo,
    )


@integraciones_admin_bp.route("/")
def listar():
    return _render_lista()



@integraciones_admin_bp.route("/emitir", methods=["POST"])
def emitir():
    sistema = request.form.get("sistema", "").strip()
    try:
        dias = int(request.form.get("vigencia", ""))
    except ValueError:
        dias = None

    if not sistema:
        flash("Indicá el sistema externo.", "error")
        return redirect(url_for(".listar"))
    if dias not in VIGENCIAS:
        flash("Elegí una vigencia válida.", "error")
        return redirect(url_for(".listar"))

    registro, token = TokenAPI.emitir(sistema[:150], dias, current_user)
    db.session.add(registro)
    db.session.commit()

    # Se muestra directamente (sin redirect ni flash) para que el token
    # no quede guardado en ningún lado: se ve una sola vez.
    return _render_lista(token_nuevo=token, sistema_nuevo=registro.sistema)



@integraciones_admin_bp.route("/<int:token_id>/revocar", methods=["POST"])
def revocar(token_id):
    registro = db.get_or_404(TokenAPI, token_id)
    if registro.esta_revocado:
        flash("Ese token ya estaba revocado.", "error")
    else:
        registro.fecha_revocacion = datetime.utcnow()
        db.session.commit()
        flash(f"Token de «{registro.sistema}» revocado.", "success")
    return redirect(url_for(".listar"))