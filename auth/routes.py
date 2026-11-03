import math
import os
from datetime import datetime, timedelta

from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user

from models import MAX_INTENTOS, MINUTOS_BLOQUEO, ROL_ADMIN, ROL_CLIENTE, Usuario, db

load_dotenv()

auth_bp = Blueprint("auth", __name__)
oauth = OAuth()

google = oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

# Mensaje único para contraseña incorrecta o correo inexistente (HU-02)
MENSAJE_GENERICO = "Correo o contraseña incorrectos."
MENSAJE_BAJA = "Tu cuenta fue dada de baja. Contactá a un administrador."


def _destino(usuario):
    return url_for("admin_dashboard" if usuario.es_admin else "panel")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(_destino(current_user))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        usuario = Usuario.query.filter_by(email=email).first()

        # 1) ¿La cuenta está bloqueada por intentos fallidos?
        if usuario and usuario.bloqueado_hasta:
            if usuario.esta_bloqueado:
                segundos = (usuario.bloqueado_hasta - datetime.utcnow()).total_seconds()
                minutos = max(1, math.ceil(segundos / 60))
                flash(f"Demasiados intentos fallidos. Probá de nuevo en {minutos} minutos.", "error")
                return render_template("auth/login.html", email=email)
            # El bloqueo ya venció: se empieza de cero
            usuario.bloqueado_hasta = None
            usuario.intentos_fallidos = 0

        # 2) Contraseña incorrecta o correo inexistente: mensaje genérico
        if not usuario or not usuario.check_password(password):
            if usuario:
                usuario.intentos_fallidos = (usuario.intentos_fallidos or 0) + 1
                if usuario.intentos_fallidos >= MAX_INTENTOS:
                    usuario.bloqueado_hasta = datetime.utcnow() + timedelta(minutes=MINUTOS_BLOQUEO)
                    usuario.intentos_fallidos = 0
                db.session.commit()
            flash(MENSAJE_GENERICO, "error")
            return render_template("auth/login.html", email=email)

        # 3) Credenciales válidas, pero la cuenta está dada de baja
        if not usuario.activo:
            flash(MENSAJE_BAJA, "error")
            return render_template("auth/login.html", email=email)

        # 4) Todo bien: se abre la sesión
        usuario.intentos_fallidos = 0
        usuario.bloqueado_hasta = None
        db.session.commit()
        login_user(usuario)
        return redirect(_destino(usuario))

    return render_template("auth/login.html")


@auth_bp.route("/login/google")
def login_google():
    return google.authorize_redirect(url_for("auth.authorize", _external=True))


@auth_bp.route("/authorize")
def authorize():
    token = google.authorize_access_token()
    info = token.get("userinfo") or google.userinfo()

    if not info.get("email_verified", True):
        flash("Tu correo de Google no está verificado.", "error")
        return redirect(url_for("auth.login"))

    email = info["email"].lower()
    usuario = (
        Usuario.query.filter_by(google_id=info["sub"]).first()
        or Usuario.query.filter_by(email=email).first()
    )
    if not usuario:
        usuario = Usuario(
            email=email,
            nombre=info.get("given_name") or info.get("name") or email,
            apellido=info.get("family_name"),
            rol=ROL_CLIENTE,
        )
        db.session.add(usuario)

    usuario.google_id = info["sub"]
    if email == os.getenv("ADMIN_EMAIL", "").lower():
        usuario.rol = ROL_ADMIN
    db.session.commit()

    if not usuario.activo:
        flash(MENSAJE_BAJA, "error")
        return redirect(url_for("auth.login"))

    login_user(usuario)
    return redirect(_destino(usuario))

@auth_bp.route("/registro", methods=["GET", "POST"])
def registro():
    if current_user.is_authenticated:
        return redirect(_destino(current_user))

    if request.method == "POST":
        datos = {
            "nombre": request.form.get("nombre", "").strip(),
            "apellido": request.form.get("apellido", "").strip(),
            "email": request.form.get("email", "").strip().lower(),
            "telefono": request.form.get("telefono", "").strip(),
        }
        password = request.form.get("password", "")
        repetir = request.form.get("repetir", "")

        error = None
        if not datos["nombre"] or not datos["apellido"] or not datos["email"]:
            error = "Completá nombre, apellido y correo."
        elif len(password) < 8:
            error = "La contraseña debe tener al menos 8 caracteres."
        elif password != repetir:
            error = "Las contraseñas no coinciden."
        elif Usuario.query.filter_by(email=datos["email"]).first():
            error = "Ese correo ya está registrado."

        if error:
            flash(error, "error")
            return render_template("auth/registro.html", **datos)

        # El rol siempre es cliente: nunca se toma del formulario
        usuario = Usuario(rol=ROL_CLIENTE, **datos)
        usuario.set_password(password)
        db.session.add(usuario)
        db.session.commit()

        login_user(usuario)
        return redirect(_destino(usuario))

    return render_template("auth/registro.html")