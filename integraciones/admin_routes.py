"""HU-21: emitir y revocar tokens de API para sistemas externos."""
from flask import Blueprint, abort, redirect, render_template, url_for
from flask_login import current_user

from models import TokenAPI

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