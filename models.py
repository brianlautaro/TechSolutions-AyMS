from datetime import datetime

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()

# Valores posibles (así no escribimos textos sueltos por todo el código)
ROL_CLIENTE = "cliente"
ROL_ADMIN = "admin"

ESTADO_PENDIENTE = "pendiente"
ESTADO_EN_CURSO = "en_curso"
ESTADO_RECHAZADA = "rechazada"
ESTADO_REALIZADO = "realizado"

MAX_INTENTOS = 5        # HU-02: cinco intentos fallidos
MINUTOS_BLOQUEO = 15    # HU-02: bloqueo de 15 minutos


class Plan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)  # Básico, Profesional, Premium
    tiempo_respuesta_horas = db.Column(db.Integer)
    activo = db.Column(db.Boolean, default=True)


class Usuario(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100))
    email = db.Column(db.String(200), unique=True, nullable=False)
    telefono = db.Column(db.String(30))          # solo lo usa el cliente
    password_hash = db.Column(db.String(255))    # vacío si entra solo con Google
    google_id = db.Column(db.String(100), unique=True)
    rol = db.Column(db.String(20), default=ROL_CLIENTE, nullable=False)
    activo = db.Column(db.Boolean, default=True)  # False = cuenta dada de baja
    intentos_fallidos = db.Column(db.Integer, default=0)
    bloqueado_hasta = db.Column(db.DateTime)
    fecha_alta = db.Column(db.DateTime, default=datetime.utcnow)
    plan_id = db.Column(db.Integer, db.ForeignKey("plan.id"))
    plan = db.relationship("Plan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return bool(self.password_hash) and check_password_hash(self.password_hash, password)

    @property
    def es_admin(self):
        return self.rol == ROL_ADMIN

    @property
    def esta_bloqueado(self):
        return self.bloqueado_hasta is not None and self.bloqueado_hasta > datetime.utcnow()


class Servicio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    descripcion = db.Column(db.String(500))
    activo = db.Column(db.Boolean, default=True)


class ServicioContratado(db.Model):
    """Qué servicios tiene contratados cada cliente (para 'Mis servicios')."""
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    servicio_id = db.Column(db.Integer, db.ForeignKey("servicio.id"), nullable=False)
    fecha_alta = db.Column(db.DateTime, default=datetime.utcnow)
    activo = db.Column(db.Boolean, default=True)
    usuario = db.relationship("Usuario", backref="servicios_contratados")
    servicio = db.relationship("Servicio")


class Solicitud(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    servicio_id = db.Column(db.Integer, db.ForeignKey("servicio.id"), nullable=False)
    tipo_modificacion = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    estado = db.Column(db.String(20), default=ESTADO_PENDIENTE, nullable=False)
    prioridad = db.Column(db.String(10))          # alta / media / baja
    fecha_ingreso = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_resolucion = db.Column(db.DateTime)
    motivo_rechazo = db.Column(db.String(300))
    usuario = db.relationship("Usuario", backref="solicitudes")
    servicio = db.relationship("Servicio")