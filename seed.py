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

    # --- Datos de prueba por persona: cada uno agrega los suyos solo en su seccion ---
    # (Los imports nuevos van dentro de la seccion. Ya existen: planes, servicios,
    #  admin, mariana, gustavo, carla, lucas.)
    # --- Valentina ---

    # --- Franco ---

    # --- Abril ---

    # --- Brian ---

    # --- Aristides ---

        # Más clientes, para probar bandeja, filtros, reportes y planes
    from models import ESTADO_RECHAZADA

    extra = [
        ("Sofía", "Ramos", "sofia@ejemplo.com", "Premium"),
        ("Tomás", "Peralta", "tomas@ejemplo.com", "Profesional"),
        ("Julieta", "Navarro", "julieta@ejemplo.com", "Básico"),
        ("Martín", "Suárez", "martin@ejemplo.com", "Profesional"),
    ]
    clientes_extra = []
    for nombre, apellido, email, plan in extra:
        u = Usuario(nombre=nombre, apellido=apellido, email=email,
                    telefono="+54 911 3333 4444", rol=ROL_CLIENTE, plan=planes[plan])
        u.set_password(DEMO_PASSWORD)
        db.session.add(u)
        clientes_extra.append(u)
    sofia, tomas, julieta, martin = clientes_extra

    db.session.add_all([
        ServicioContratado(usuario=sofia, servicio=servicios[2]),
        ServicioContratado(usuario=sofia, servicio=servicios[5]),
        ServicioContratado(usuario=tomas, servicio=servicios[4]),
        ServicioContratado(usuario=tomas, servicio=servicios[6]),
        ServicioContratado(usuario=julieta, servicio=servicios[7]),
        ServicioContratado(usuario=martin, servicio=servicios[0]),
        ServicioContratado(usuario=martin, servicio=servicios[1]),
    ])

    # Solicitudes en todos los estados y prioridades, con fechas distintas
    db.session.add_all([
        Solicitud(usuario=sofia, servicio=servicios[2], tipo_modificacion="Cambio de horario",
                  descripcion="Mover las entrevistas a la tarde.", estado=ESTADO_PENDIENTE,
                  prioridad="alta", fecha_ingreso=ahora - timedelta(hours=3)),
        Solicitud(usuario=sofia, servicio=servicios[5], tipo_modificacion="Ampliación del alcance",
                  descripcion="Sumar un modelo de predicción de ventas.", estado=ESTADO_EN_CURSO,
                  prioridad="media", fecha_ingreso=ahora - timedelta(days=2)),
        Solicitud(usuario=tomas, servicio=servicios[4], tipo_modificacion="Cambio de plan",
                  descripcion="Pasar al plan Premium.", estado=ESTADO_RECHAZADA,
                  prioridad="baja", fecha_ingreso=ahora - timedelta(days=4),
                  fecha_resolucion=ahora - timedelta(days=3),
                  motivo_rechazo="El cambio de plan se gestiona por administración."),
        Solicitud(usuario=tomas, servicio=servicios[6], tipo_modificacion="Cambio de horario",
                  descripcion="Capacitación los viernes.", estado=ESTADO_REALIZADO,
                  prioridad="media", fecha_ingreso=ahora - timedelta(days=9),
                  fecha_resolucion=ahora - timedelta(days=6)),
        Solicitud(usuario=julieta, servicio=servicios[7], tipo_modificacion="Ampliación del alcance",
                  descripcion="Incluir normativa de protección de datos.", estado=ESTADO_PENDIENTE,
                  prioridad="media", fecha_ingreso=ahora - timedelta(days=1)),
        Solicitud(usuario=martin, servicio=servicios[0], tipo_modificacion="Cambio de horario",
                  descripcion="Reunión mensual a primera hora.", estado=ESTADO_PENDIENTE,
                  prioridad="baja", fecha_ingreso=ahora - timedelta(days=5)),
        Solicitud(usuario=martin, servicio=servicios[1], tipo_modificacion="Ampliación del alcance",
                  descripcion="Agregar campaña en LinkedIn.", estado=ESTADO_REALIZADO,
                  prioridad="alta", fecha_ingreso=ahora - timedelta(days=12),
                  fecha_resolucion=ahora - timedelta(days=10)),
    ])

    db.session.commit()
    print("Datos de prueba listos.")


if __name__ == '__main__':
    from app import app
    with app.app_context():
        run_seed()