import hashlib
import secrets
from datetime import datetime, timedelta

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

PRIORIDAD_ALTA = "alta"
PRIORIDAD_MEDIA = "media"
PRIORIDAD_BAJA = "baja"
PRIORIDADES = [PRIORIDAD_ALTA, PRIORIDAD_MEDIA, PRIORIDAD_BAJA]


class Plan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)  # Básico, Profesional, Premium
    tiempo_respuesta_horas = db.Column(db.Integer)
    activo = db.Column(db.Boolean, default=True)
    
    @property
    def prioridad_sugerida(self):
        """HU-12: menos horas de respuesta = más prioridad (Premium 24h, Profesional 48h, Básico 72h)."""
        horas = self.tiempo_respuesta_horas
        if horas is None:
            return None
        if horas <= 24:
            return PRIORIDAD_ALTA
        if horas <= 48:
            return PRIORIDAD_MEDIA
        return PRIORIDAD_BAJA


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
    prioridad_modificada_por_id = db.Column(db.Integer, db.ForeignKey("usuario.id"))  # HU-12
    fecha_cambio_prioridad = db.Column(db.DateTime)                                   # HU-12
    usuario = db.relationship("Usuario", foreign_keys=[usuario_id], backref="solicitudes")
    prioridad_modificada_por = db.relationship("Usuario", foreign_keys=[prioridad_modificada_por_id])
    servicio = db.relationship("Servicio")
    
    @property
    def admite_cambio_prioridad(self):
        """HU-12: no se cambia la prioridad de solicitudes finalizadas o rechazadas."""
        return self.estado not in (ESTADO_REALIZADO, ESTADO_RECHAZADA)



class TokenAPI(db.Model):
    """HU-21: token de acceso para un sistema externo (lo usa la API de HU-22).

    Nunca se guarda el token en texto plano: solo su hash SHA-256 y los
    primeros caracteres, para poder reconocerlo en la lista.
    """
    id = db.Column(db.Integer, primary_key=True)
    sistema = db.Column(db.String(150), nullable=False)       # sistema externo asociado
    token_hash = db.Column(db.String(64), unique=True, nullable=False)
    prefijo = db.Column(db.String(12), nullable=False)        # ej. "tsk_a1b2" (se muestra en la lista)
    fecha_emision = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    fecha_vencimiento = db.Column(db.DateTime, nullable=False)
    ultimo_uso = db.Column(db.DateTime)                       # lo actualiza la API (HU-22)
    fecha_revocacion = db.Column(db.DateTime)                 # si tiene valor, está revocado
    ventana_inicio = db.Column(db.DateTime)                   # HU-22: inicio de la hora actual
    consultas_en_ventana = db.Column(db.Integer, default=0)   # HU-22: consultas en esa hora
    emitido_por_id = db.Column(db.Integer, db.ForeignKey("usuario.id"))
    emitido_por = db.relationship("Usuario")

    PREFIJO_TOKEN = "tsk_"
    LIMITE_POR_HORA = 100

    @staticmethod
    def calcular_hash(token):
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    @classmethod
    def emitir(cls, sistema, dias_vigencia, admin):
        """Crea el token y devuelve (registro, token_en_texto_plano).

        El texto plano solo existe en este momento: se muestra una vez y se pierde.
        """
        token = cls.PREFIJO_TOKEN + secrets.token_urlsafe(32)
        registro = cls(
            sistema=sistema,
            token_hash=cls.calcular_hash(token),
            prefijo=token[:8],
            fecha_vencimiento=datetime.utcnow() + timedelta(days=dias_vigencia),
            emitido_por=admin,
        )
        return registro, token

    @classmethod
    def buscar_valido(cls, token):
        """Para HU-22: devuelve el token si existe, no fue revocado y está vigente."""
        if not token:
            return None
        registro = cls.query.filter_by(token_hash=cls.calcular_hash(token)).first()
        return registro if registro and registro.esta_vigente else None

    @property
    def esta_revocado(self):
        return self.fecha_revocacion is not None

    @property
    def esta_vencido(self):
        return self.fecha_vencimiento <= datetime.utcnow()

    @property
    def esta_vigente(self):
        return not self.esta_revocado and not self.esta_vencido

    @property
    def estado(self):
        if self.esta_revocado:
            return "Revocado"
        if self.esta_vencido:
            return "Vencido"
        return "Vigente"

    def registrar_consulta(self):
        """HU-22: cuenta una consulta. Devuelve False si ya superó el límite de la hora."""
        ahora = datetime.utcnow()
        if not self.ventana_inicio or ahora - self.ventana_inicio >= timedelta(hours=1):
            self.ventana_inicio = ahora
            self.consultas_en_ventana = 0
        if self.consultas_en_ventana >= self.LIMITE_POR_HORA:
            return False
        self.consultas_en_ventana += 1
        self.ultimo_uso = ahora
        return True