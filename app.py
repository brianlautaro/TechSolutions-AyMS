import os

from solicitudes.admin_routes import consultar_bandeja, solicitudes_admin_bp
from integraciones.admin_routes import integraciones_admin_bp
from api.routes import api_bp
from dotenv import load_dotenv
from flask import Flask, abort, redirect, render_template, request, session, url_for
from flask_login import LoginManager, current_user, login_required, logout_user
from reportes.admin_routes import reportes_admin_bp
from solicitudes.cliente_routes import solicitudes_cliente_bp
from auth.routes import auth_bp, oauth
from models import ESTADO_PENDIENTE, ESTADOS, PRIORIDADES, ServicioContratado, Solicitud, Usuario, db

# --- Imports por persona: cada uno agrega los suyos solo en su seccion ---
# --- Valentina ---

# --- Franco ---

from adjuntos.routes import adjuntos_bp
from mis_solicitudes.routes import mis_solicitudes_bp # HU-10: el cliente consulta el estado de sus solicitudes (solo lectura).


# --- Abril ---
from servicios.admin_routes import servicios_admin_bp  # HU-20: gestionar servicios

from planes.admin_routes import planes_admin_bp  # HU-19: gestionar planes
# --- Brian ---

# --- Aristides ---
from reclamos.admin_routes import reclamos_admin_bp  # HU-17: responder reclamos
from reclamos.clientes_route import reclamos_cliente_bp  # HU-16 (Brian): ver el registro más abajo

from clientes.admin_routes import clientes_admin_bp  # HU-18: gestionar clientes

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

app.config["GOOGLE_CLIENT_ID"] = os.getenv("GOOGLE_CLIENT_ID")
app.config["GOOGLE_CLIENT_SECRET"] = os.getenv("GOOGLE_CLIENT_SECRET")
oauth.init_app(app)

database_url = os.getenv("DATABASE_URL", "sqlite:///techsolutions.db")
# Render entrega URLs con el prefijo "postgres://" pero SQLAlchemy requiere "postgresql://"
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()
    # Datos de prueba automáticos si la base está vacía
    if Usuario.query.count() == 0:
        from seed import run_seed
        run_seed()

login_manager = LoginManager(app)
login_manager.login_view = "auth.login"

app.register_blueprint(auth_bp)
app.register_blueprint(solicitudes_admin_bp)
app.register_blueprint(integraciones_admin_bp)
app.register_blueprint(api_bp)
app.register_blueprint(reportes_admin_bp)
app.register_blueprint(solicitudes_cliente_bp)


# --- Blueprints por persona: cada uno registra los suyos solo en su seccion ---
# --- Valentina ---

# --- Franco ---

app.register_blueprint(adjuntos_bp)

app.register_blueprint(mis_solicitudes_bp) # HU-10: el cliente consulta el estado de sus solicitudes (solo lectura).


# --- Abril ---
app.register_blueprint(servicios_admin_bp)  # HU-20: gestionar servicios
app.register_blueprint(planes_admin_bp)  # HU-19: gestionar planes

# --- Brian ---

# --- Aristides ---
app.register_blueprint(reclamos_admin_bp)  # HU-17: responder reclamos
# HU-16 (Brian) quedó sin registrar y /reclamos/nuevo daba 404. Si Brian lo registra en su
# sección, este chequeo evita registrarlo dos veces.
if "reclamos_cliente" not in app.blueprints:
    app.register_blueprint(reclamos_cliente_bp)

app.register_blueprint(clientes_admin_bp)  # HU-18: gestionar clientes


@login_manager.user_loader
def load_user(user_id):
    usuario = db.session.get(Usuario, int(user_id))
    # Una cuenta dada de baja pierde la sesión
    return usuario if usuario and usuario.activo else None


@app.context_processor
def inject_globals():
    return {"is_admin": current_user.is_authenticated and current_user.es_admin}


@app.errorhandler(403)
def forbidden(_e):
    return render_template("403.html"), 403


# ----------------------------------------
# RUTAS PRINCIPALES
# ----------------------------------------
@app.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for("admin_dashboard" if current_user.es_admin else "panel"))
    return redirect(url_for("auth.login"))



@app.route("/panel")
@login_required
def panel():
    # Panel del cliente. Lo completan HU-02 (login) y HU-06 (mis servicios).
    
    return render_template("panel.html")

@app.route("/mis-servicios")
@login_required
def mis_servicios():
    contratados = (
        ServicioContratado.query
        .filter_by(usuario_id=current_user.id)
        .order_by(ServicioContratado.fecha_alta.desc())
        .all()
    )
    return render_template("mis_servicios.html", contratados=contratados)

@app.route("/admin")
@login_required
def admin_dashboard():
    if not current_user.es_admin:
        abort(403)
    # HU-11: bandeja de solicitudes con filtros
    solicitudes, filtros = consultar_bandeja(request.args)
    hay_pendientes = Solicitud.query.filter_by(estado=ESTADO_PENDIENTE).count() > 0
    return render_template(
        "admin/dashboard.html",
        solicitudes=solicitudes,
        filtros=filtros,
        estados=ESTADOS,
        prioridades=PRIORIDADES,
        hay_pendientes=hay_pendientes,
    )


@app.route("/logout")
@login_required
def logout():
    logout_user()
    session.clear()
    return redirect(url_for("home"))

@app.after_request
def no_guardar_en_cache(respuesta):
    # HU-03: si hay sesión abierta, el navegador no guarda copia de la página.
    # Así, después de cerrar sesión, el botón "atrás" vuelve a pedirla al servidor
    # y este redirige al login.
    if current_user.is_authenticated and request.endpoint != "static":
        respuesta.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    return respuesta


if __name__ == "__main__":
    app.run(debug=True)