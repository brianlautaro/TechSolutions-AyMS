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
ESTADOS = [ESTADO_PENDIENTE, ESTADO_EN_CURSO, ESTADO_RECHAZADA, ESTADO_REALIZADO]

MAX_INTENTOS = 5        # HU-02: cinco intentos fallidos
MINUTOS_BLOQUEO = 15    # HU-02: bloqueo de 15 minutos

PRIORIDAD_ALTA = "alta"
PRIORIDAD_MEDIA = "media"
PRIORIDAD_BAJA = "baja"
PRIORIDADES = [PRIORIDAD_ALTA, PRIORIDAD_MEDIA, PRIORIDAD_BAJA]


# HU-08: tipos de modificación que el cliente puede elegir en el formulario.
TIPOS_MODIFICACION = [
    "Cambio de horario",
    "Ampliación del alcance",
    "Reducción del alcance",
    "Cambio de responsable",
    "Otro",
]

# HU-08: solicitudes de modificación que incluye cada plan por mes.
CREDITOS_POR_PLAN = {
    "Básico": 2,
    "Profesional": 5,
    "Premium": 10,
}

# Gestión de notificaciones (diccionario de datos: Evento_notificacion)
EVENTO_NUEVA_SOLICITUD = "nueva_solicitud"
CANAL_EMAIL = "email"

EVENTO_NUEVO_RECLAMO = "nuevo_reclamo"   # HU-16

# HU-16 / HU-17: estados de un reclamo
RECLAMO_PENDIENTE = "pendiente"
RECLAMO_EN_REVISION = "en_revision"   # lo usa HU-17
RECLAMO_RESPONDIDO = "respondido"     # lo usa HU-17
ESTADOS_RECLAMO = [RECLAMO_PENDIENTE, RECLAMO_EN_REVISION, RECLAMO_RESPONDIDO]

class Plan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)  # Básico, Profesional, Premium
    tiempo_respuesta_horas = db.Column(db.Integer)
    activo = db.Column(db.Boolean, default=True)
    creditos = db.Column(db.Integer)                                            # HU-19 (Abril)
    modificado_por_id = db.Column(db.Integer, db.ForeignKey("usuario.id"))      # HU-19 (Abril)
    fecha_modificacion = db.Column(db.DateTime)                                 # HU-19 (Abril)
    modificado_por = db.relationship("Usuario", foreign_keys=[modificado_por_id])
    
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

    
    @property
    def creditos_mensuales(self):
        """HU-08: cuántas solicitudes de modificación incluye el plan por mes."""
        return CREDITOS_POR_PLAN.get(self.nombre, 0)


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
    plan = db.relationship("Plan", foreign_keys=[plan_id])  # Plan también tiene FK a usuario (HU-19)
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
    
    @property
    def servicios_activos(self):
        """HU-08: servicios contratados sobre los que se pueden abrir solicitudes."""
        return [
            c for c in self.servicios_contratados
            if c.activo and c.servicio.activo
        ]

    @property
    def creditos_usados(self):
        """HU-08: solicitudes del mes en curso. Las rechazadas devuelven el crédito."""
        hoy = datetime.utcnow()
        inicio_mes = datetime(hoy.year, hoy.month, 1)
        return (
            Solicitud.query
            .filter(
                Solicitud.usuario_id == self.id,
                Solicitud.fecha_ingreso >= inicio_mes,
                Solicitud.estado != ESTADO_RECHAZADA,
            )
            .count()
        )

    @property
    def creditos_restantes(self):
        """HU-08: saldo del mes. Sin plan, no hay créditos."""
        if not self.plan:
            return 0
        return max(0, self.plan.creditos_mensuales - self.creditos_usados)

class Servicio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    categoria = db.Column(db.String(100))                                  # HU-20
    descripcion = db.Column(db.String(500))
    activo = db.Column(db.Boolean, default=True)
    fecha_modificacion = db.Column(db.DateTime)                            # HU-20: último cambio
    modificado_por_id = db.Column(db.Integer, db.ForeignKey("usuario.id"))  # HU-20: quién lo hizo
    modificado_por = db.relationship("Usuario")


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



class Notificacion(db.Model):
    """Registro de notificaciones (diccionario de datos: Registro_notificacion).
    HU-08 lo usa para avisar al administrador de una nueva solicitud (simula NotiSys)."""
    id = db.Column(db.Integer, primary_key=True)
    destinatario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey("usuario.id"))
    solicitud_id = db.Column(db.Integer, db.ForeignKey("solicitud.id"))
    reclamo_id = db.Column(db.Integer, db.ForeignKey("reclamo.id"))
    tipo_evento = db.Column(db.String(40), nullable=False)
    mensaje = db.Column(db.String(300), nullable=False)
    canal = db.Column(db.String(20), default=CANAL_EMAIL, nullable=False)
    fecha_envio = db.Column(db.DateTime, default=datetime.utcnow)
    leida = db.Column(db.Boolean, default=False)
    destinatario = db.relationship("Usuario", foreign_keys=[destinatario_id])
    cliente = db.relationship("Usuario", foreign_keys=[cliente_id])
    solicitud = db.relationship("Solicitud")
    reclamo = db.relationship("Reclamo")

class Reclamo(db.Model):
    """HU-16: reclamo de un cliente. Lo revisa y responde el administrador (HU-17)."""
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    servicio_id = db.Column(db.Integer, db.ForeignKey("servicio.id"))      # opcional
    solicitud_id = db.Column(db.Integer, db.ForeignKey("solicitud.id"))    # opcional
    descripcion = db.Column(db.Text, nullable=False)
    estado = db.Column(db.String(20), default=RECLAMO_PENDIENTE, nullable=False)
    fecha_ingreso = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    usuario = db.relationship("Usuario", backref="reclamos")
    servicio = db.relationship("Servicio")
    solicitud = db.relationship("Solicitud")

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


# =====================================================================
# MODELOS POR PERSONA (Bloques 2 y 3)
# Cada uno agrega sus constantes, imports y clases SOLO dentro de su
# seccion (un import nuevo va dentro de la seccion, no arriba del archivo).
# Si necesitas una columna nueva en un modelo que ya existe (Usuario,
# Solicitud, Plan...), avisa en el grupo: todos tienen que borrar
# instance\techsolutions.db.
# =====================================================================

# --- Valentina ---
# HU-05: aviso al administrador cuando un cliente contrata un servicio
EVENTO_NUEVA_CONTRATACION = "nueva_contratacion"


# --- Franco ---
# HU-23: registro de la actividad de los clientes (solo se agrega, nunca se modifica)
ACCION_INICIO_SESION = "inicio_sesion"
ACCION_SOLICITUD = "solicitud_abierta"
ACCION_ADJUNTO = "archivo_adjuntado"
ACCION_RECLAMO = "reclamo_presentado"


class ActividadCliente(db.Model):
    __tablename__ = "actividad_cliente"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    tipo_accion = db.Column(db.String(30), nullable=False)
    detalle = db.Column(db.String(200))
    fecha = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    usuario = db.relationship("Usuario")
    
# HU-09: archivos adjuntos de una solicitud
ESTADOS_CON_CARGA = (ESTADO_PENDIENTE, ESTADO_EN_CURSO)   # en estos estados se puede subir
MAX_ADJUNTOS = 5                                          # archivos por solicitud
MAX_BYTES_ADJUNTO = 5 * 1024 * 1024                       # 5 MB
EXTENSIONES_ADJUNTO = {"pdf", "jpg", "jpeg", "png"}


class Adjunto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    solicitud_id = db.Column(db.Integer, db.ForeignKey("solicitud.id"), nullable=False)
    nombre_original = db.Column(db.String(255), nullable=False)   # el que ve el cliente
    nombre_guardado = db.Column(db.String(255), nullable=False)   # el nombre real en el disco
    tamano_bytes = db.Column(db.Integer, nullable=False)
    fecha_carga = db.Column(db.DateTime, default=datetime.utcnow)
    solicitud = db.relationship("Solicitud", backref="adjuntos")

# --- Abril ---
# --- HU-07: solicitar cambio de plan ---
# Tabla nueva (no cambia ninguna existente): db.create_all() la crea sola,
# no hace falta borrar instance\techsolutions.db.
# Diccionario de datos: Solicitud_cambio_plan = @ID_Cliente + Plan_actual +
#                       Plan_solicitado + Fecha_solicitud + (Motivo)
EVENTO_CAMBIO_PLAN = "cambio_de_plan"     # DD: Tipo_evento "Cambio_de_plan"
ORIGEN_WEB = "web"
ORIGEN_WHATSAPP = "whatsapp"              # canal de WhatsApp Business (release posterior)
MAX_MOTIVO_CAMBIO_PLAN = 300


class SolicitudCambioPlan(db.Model):
    """HU-07 / CU-09: pedido del cliente para pasar a otro plan.

    Estados (los mismos del DD para solicitudes):
    pendiente -> realizado (el admin lo aprueba y se aplica el plan nuevo)
    pendiente -> rechazada (el admin lo rechaza con un motivo)
    """
    __tablename__ = "solicitud_cambio_plan"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    plan_actual_id = db.Column(db.Integer, db.ForeignKey("plan.id"))
    plan_solicitado_id = db.Column(db.Integer, db.ForeignKey("plan.id"), nullable=False)
    motivo = db.Column(db.String(MAX_MOTIVO_CAMBIO_PLAN))           # opcional
    estado = db.Column(db.String(20), default=ESTADO_PENDIENTE, nullable=False)
    origen = db.Column(db.String(20), default=ORIGEN_WEB, nullable=False)
    fecha_solicitud = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    fecha_resolucion = db.Column(db.DateTime)
    motivo_rechazo = db.Column(db.String(300))
    resuelta_por_id = db.Column(db.Integer, db.ForeignKey("usuario.id"))

    usuario = db.relationship("Usuario", foreign_keys=[usuario_id], backref="cambios_de_plan")
    plan_actual = db.relationship("Plan", foreign_keys=[plan_actual_id])
    plan_solicitado = db.relationship("Plan", foreign_keys=[plan_solicitado_id])
    resuelta_por = db.relationship("Usuario", foreign_keys=[resuelta_por_id])

    @classmethod
    def pendiente_de(cls, usuario):
        """Criterio 4 de HU-07: la solicitud de cambio pendiente del cliente, si tiene una."""
        return cls.query.filter_by(usuario_id=usuario.id, estado=ESTADO_PENDIENTE).first()
# --- Brian ---

# --- Aristides ---

# HU-17: eventos de notificación al cliente por un reclamo y largo máximo de la respuesta
EVENTO_RECLAMO_EN_REVISION = "reclamo_en_revision"
EVENTO_RECLAMO_RESPONDIDO = "reclamo_respondido"
MAX_RESPUESTA_RECLAMO = 1000


class RespuestaReclamo(db.Model):
    """HU-17: respuesta del administrador a un reclamo (una por reclamo)."""
    __tablename__ = "respuesta_reclamo"

    id = db.Column(db.Integer, primary_key=True)
    reclamo_id = db.Column(db.Integer, db.ForeignKey("reclamo.id"), nullable=False, unique=True)
    admin_id = db.Column(db.Integer, db.ForeignKey("usuario.id"))
    texto = db.Column(db.Text, nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # "respuesta" queda disponible como reclamo.respuesta (sin tocar la clase Reclamo)
    reclamo = db.relationship("Reclamo", backref=db.backref("respuesta", uselist=False))
    admin = db.relationship("Usuario")

# HU-18: acciones que el administrador hace sobre la cuenta de un cliente
ACCION_CLIENTE_EDICION = "edicion"
ACCION_CLIENTE_BAJA = "baja"


class HistorialCliente(db.Model):
    """HU-18: registro de cambios del administrador sobre un cliente (fecha de cada modificación)."""
    __tablename__ = "historial_cliente"

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey("usuario.id"))
    accion = db.Column(db.String(20), nullable=False)
    detalle = db.Column(db.String(300), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    cliente = db.relationship("Usuario", foreign_keys=[cliente_id])
    admin = db.relationship("Usuario", foreign_keys=[admin_id])
