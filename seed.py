"""
Script para cargar datos de prueba de Tech Solutions.
Uso: python seed.py
"""
import os
from datetime import datetime, timedelta

from models import (
    db, Plan, Usuario, Servicio, ServicioContratado, Solicitud,
    ROL_ADMIN, ROL_CLIENTE,
    ESTADO_PENDIENTE, ESTADO_EN_CURSO, ESTADO_REALIZADO,
)

# Contraseña de las cuentas de prueba. Solo para desarrollo, nunca para producción.
DEMO_PASSWORD = "Demo1234!"

PLANES = [
    {"nombre": "Básico", "tiempo_respuesta_horas": 72},
    {"nombre": "Profesional", "tiempo_respuesta_horas": 48},
    {"nombre": "Premium", "tiempo_respuesta_horas": 24},
]

SERVICIOS = [
    ("Finanzas y Contabilidad", "Asesoría en gestión financiera y tributaria."),
    ("Marketing Digital", "Estrategias de publicidad y posicionamiento en redes sociales."),
    ("Recursos Humanos y Talento", "Selección y capacitación de personal."),
    ("Desarrollo Web y UX/UI", "Diseño y optimización de plataformas digitales."),
    ("Logística y Cadena de Suministro", "Gestión de inventario y distribución."),
    ("Inteligencia Artificial y Machine Learning", "Soluciones de IA para automatizar procesos."),
    ("Gestión de Proyectos Agile", "Capacitación y soporte en metodologías ágiles."),
    ("Cumplimiento Legal y Normativo", "Asesoría en normativas legales de cada sector."),
]


def run_seed():
    """Ejecutar dentro de un app_context activo."""
    if Usuario.query.count() > 0:
        return

    print("Cargando datos de prueba de Tech Solutions...")

    planes = {}
    for p in PLANES:
        plan = Plan(**p)
        db.session.add(plan)
        planes[p["nombre"]] = plan

    servicios = []
    for nombre, descripcion in SERVICIOS:
        servicio = Servicio(nombre=nombre, descripcion=descripcion)
        db.session.add(servicio)
        servicios.append(servicio)

    admin = Usuario(
        nombre="Admin",
        apellido="Tech Solutions",
        email=os.getenv("ADMIN_EMAIL", "admin@techsolutions.com").lower(),
        rol=ROL_ADMIN,
    )
    mariana = Usuario(
        nombre="Mariana", apellido="Díaz", email="mariana@ejemplo.com",
        telefono="+54 911 1111 1111", rol=ROL_CLIENTE, plan=planes["Premium"],
    )
    gustavo = Usuario(
        nombre="Gustavo", apellido="Coria", email="gustavo@ejemplo.com",
        telefono="+54 911 2222 3333", rol=ROL_CLIENTE, plan=planes["Profesional"],
    )
    # Cuenta dada de baja: sirve para probar el caso "cuenta inactiva" de la HU-02
    baja = Usuario(
        nombre="Cuenta", apellido="De Baja", email="baja@ejemplo.com",
        telefono="+54 911 2222 3333", rol=ROL_CLIENTE, plan=planes["Básico"], activo=False,
    )
    # Cuenta activa pero sin servicios contratados: sirve para probar el caso "sin servicios" de la HU-06
    carla = Usuario(
        nombre="Carla", apellido="Sinser", email="carla@ejemplo.com",
        telefono="+54 911 2222 3333", rol=ROL_CLIENTE, plan=planes["Básico"],
    )
    # Cuenta activa con servicios contratados dados de baja: sirve para probar el caso "servicios dados de baja" de la HU-06
    lucas = Usuario(
        nombre="Lucas", apellido="Conba", email="lucas@ejemplo.com",
        telefono="+54 911 2222 3333", rol=ROL_CLIENTE, plan=planes["Básico"],
    )
    for usuario in (admin, mariana, gustavo, baja, carla, lucas):
        usuario.set_password(DEMO_PASSWORD)
        db.session.add(usuario)

    db.session.add_all([
        ServicioContratado(usuario=mariana, servicio=servicios[0]),
        ServicioContratado(usuario=mariana, servicio=servicios[3]),
        ServicioContratado(usuario=gustavo, servicio=servicios[1]),
        ServicioContratado(usuario=lucas, servicio=servicios[1]),
        ServicioContratado(usuario=lucas, servicio=servicios[4], activo=False),
    ])

    ahora = datetime.utcnow()
    db.session.add_all([
        Solicitud(
            usuario=mariana, servicio=servicios[0],
            tipo_modificacion="Cambio de horario",
            descripcion="Necesito mover la reunión semanal al jueves.",
            estado=ESTADO_PENDIENTE, prioridad="alta",
        ),
        Solicitud(
            usuario=mariana, servicio=servicios[3],
            tipo_modificacion="Ampliación del alcance",
            descripcion="Sumar una sección de reservas al sitio.",
            estado=ESTADO_EN_CURSO, prioridad="media",
        ),
        Solicitud(
            usuario=gustavo, servicio=servicios[1],
            tipo_modificacion="Cambio de plan",
            descripcion="Quiero pasar al plan Premium.",
            estado=ESTADO_REALIZADO, prioridad="baja",
            fecha_resolucion=ahora - timedelta(days=1),
        ),
    ])

    db.session.commit()
    print("Datos de prueba listos.")


if __name__ == '__main__':
    from app import app
    with app.app_context():
        run_seed()