# Tutorial: cómo correr y probar Tech Solutions (HU-25)

Guía para que el cliente (Consultora Tech Solutions) pueda **instalar, ejecutar y probar** la demo sin ayuda del equipo.
Aplicación web en **Python + Flask**. Equipo "Las Cloves" – Escuela Da Vinci, Análisis y Metodología de Sistemas.

Tiempo estimado: 10 minutos la primera vez.

---

## 1. Qué necesitás

| Requisito | Detalle |
|---|---|
| Python | 3.12 o superior (se probó también con 3.13). Verificalo con `python --version`. |
| Internet | Solo para instalar las dependencias la primera vez. |
| Navegador | Cualquiera actual (Chrome, Edge, Firefox). |

No hace falta instalar ninguna base de datos: la demo usa **SQLite** y crea el archivo sola.

## 2. Instalación (Windows – PowerShell)

Abrí PowerShell **dentro de la carpeta del proyecto** (donde está `app.py`) y ejecutá:

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Si PowerShell bloquea el script de activación, corré una vez `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` y repetí el segundo comando.

**macOS / Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 3. Configuración (archivo `.env`)

1. Copiá el archivo `.env.example` y renombralo a `.env` (en la misma carpeta que `app.py`):

   ```powershell
   Copy-Item .env.example .env
   ```

2. Abrilo y dejá, como mínimo, esta línea con un valor cualquiera (es la clave que firma las sesiones):

   ```
   SECRET_KEY=cambia-esto-por-una-frase-larga-y-secreta
   ```

> **Importante:** sin `SECRET_KEY` la app arranca pero el inicio de sesión falla con un error 500.

Las demás variables son **opcionales** y no se necesitan para la demo:

| Variable | Para qué sirve |
|---|---|
| `ADMIN_EMAIL` | Correo del administrador. Por defecto: `admin@techsolutions.com`. |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | Habilitan "Ingresar con Google". Sin ellas, se ingresa con correo y contraseña. |
| `DATABASE_URL` | Usar otra base (por ejemplo PostgreSQL). Por defecto: SQLite local. |

## 4. Ejecutar

```powershell
python app.py
```

La primera vez la app crea la base de datos y carga los **datos de prueba** (verás "Cargando datos de prueba de Tech Solutions..."). Después abrí en el navegador:

**http://127.0.0.1:5000**

Para detenerla: `Ctrl + C` en la terminal.

## 5. Usuarios de prueba

Todas las cuentas usan la contraseña **`Demo1234!`**

| Rol | Correo | Para probar |
|---|---|---|
| Administrador | `admin@techsolutions.com` | Todo el panel de administración |
| Cliente | `mariana@ejemplo.com` | Plan Premium, 2 servicios activos, 2 solicitudes abiertas (el caso más completo) |
| Cliente | `gustavo@ejemplo.com` | Plan Profesional, 1 servicio |
| Cliente | `lucas@ejemplo.com` | 1 servicio activo y 1 dado de baja |
| Cliente | `carla@ejemplo.com` | Sin servicios contratados (mensaje de "sin servicios") |
| Cliente | `baja@ejemplo.com` | Cuenta dada de baja: **no** puede ingresar |
| Clientes extra | `sofia@`, `tomas@`, `julieta@`, `martin@` `ejemplo.com` | Solicitudes y reclamos en distintos estados |

## 6. Recorrido sugerido

### 6.1 Como cliente (`mariana@ejemplo.com`)

1. **Ingresar** en `/login`. Te lleva al panel del cliente.
2. **Mis servicios** (menú superior): lista los servicios contratados (HU-06).
3. **Catálogo** (`/catalogo/`): contratar un servicio nuevo (HU-05).
4. **Solicitar una modificación** (botón del panel): elegí un servicio, un tipo de cambio y una descripción. La solicitud queda en estado **pendiente** (HU-08).
5. **Mis solicitudes** (`/mis-solicitudes/`): ver el estado de cada una (HU-10). Desde ahí se **adjuntan archivos** a una solicitud abierta: PDF, JPG o PNG, hasta 5 archivos de 5 MB cada uno (HU-09).
6. **Cambiar de plan** (botón del panel, `/mi-plan/`): pedir un plan distinto. Solo se permite una solicitud pendiente a la vez (HU-07).
7. **Presentar un reclamo** (`/reclamos/nuevo`) (HU-16).
8. **Salir** (menú superior): cierra la sesión (HU-03).
9. **Crear una cuenta nueva** en `/registro`: la contraseña debe tener al menos 8 caracteres y un número (HU-01).

### 6.2 Como administrador (`admin@techsolutions.com`)

El panel de administración (`/admin`) tiene los accesos en la parte superior.

1. **Bandeja de solicitudes** (pantalla principal del admin): filtros por estado y prioridad (HU-11).
2. **Detalle de una solicitud**: entrá a una **pendiente** y pasala a **en curso** (*Aprobar*) o **rechazada** (*Rechazar*, con motivo obligatorio). Una solicitud **en curso** se **finaliza** y pasa a **realizado** (HU-14, HU-15). Desde el detalle también se cambia la **prioridad** (alta / media / baja) (HU-12).
3. **Reclamos** (`/admin/reclamos/`): marcar *en revisión* y responder; el reclamo respondido queda en modo lectura. `?ver=respondidos` muestra los ya respondidos (HU-17).
4. **Clientes** (`/admin/clientes/`): listado, ficha, edición de datos de contacto y baja. Si el cliente tiene solicitudes abiertas, la baja avisa cuántas son y pide confirmación explícita (HU-18). Probalo con `mariana@ejemplo.com` (tiene 2 abiertas).
5. **Planes** (`/admin/planes/`) y **Servicios** (`/admin/servicios/`): alta, edición, baja y desactivación (HU-19, HU-20).
6. **Actividad** (`/admin/actividad/`): acciones registradas de los clientes (inicio de sesión, solicitudes, adjuntos, reclamos) (HU-23).
7. **Integraciones** (`/admin/integraciones/`): emitir y revocar tokens de acceso para sistemas externos (HU-21).
8. **Reportes** (`/admin/reportes/`): planes, solicitudes, reclamos y actividad, por rango de fechas, con descarga en **CSV** y **PDF** (HU-24).

### 6.3 API para sistemas externos (HU-22)

1. Como admin, en **Integraciones**, emití un token (vigencia 30, 90, 180 o 365 días). **El token se muestra una sola vez**: copialo.
2. Consultá los clientes (solo lectura):

   ```powershell
   curl.exe -H "Authorization: Bearer TU_TOKEN" http://127.0.0.1:5000/api/clientes
   ```

   Devuelve JSON con los datos de contacto y plan de cada cliente (nunca contraseñas). Cada token admite hasta 100 consultas por hora; si está revocado o vencido, responde con error.

## 7. Estados de una solicitud

```
pendiente ──aprobar──▶ en curso ──finalizar──▶ realizado
    └────rechazar (con motivo)────▶ rechazada
```

El diagrama completo de estados (solicitud, reclamo, cliente, token) está en `docs/diagrama-estados.png`.

## 8. Empezar de cero (reiniciar los datos de prueba)

1. Detené la app (`Ctrl + C`).
2. Borrá el archivo `instance\techsolutions.db` (y la carpeta `uploads\` si querés quitar adjuntos).
3. Ejecutá `python app.py`: se vuelve a crear la base con los datos de prueba originales.

## 9. Problemas frecuentes

| Síntoma | Causa y solución |
|---|---|
| Error 500 al iniciar sesión | Falta `SECRET_KEY` en `.env`. Agregala y reiniciá. |
| `ModuleNotFoundError` | No está activado el entorno virtual o faltó `pip install -r requirements.txt`. |
| "No se puede borrar la base" / archivo en uso | La app sigue corriendo. Detenela con `Ctrl + C` y volvé a intentar. |
| Los estilos se ven viejos | Recargá sin caché con `Ctrl + F5`. |
| `baja@ejemplo.com` no entra | Es lo esperado: es una cuenta dada de baja de prueba. |
| El puerto 5000 está ocupado | Cerrá la otra aplicación que lo usa, o detené una copia anterior de esta. |

## 10. Notas de la demo

- Las **notificaciones** (por ejemplo, al responder un reclamo) se guardan en la base y se registran en el log de la terminal: simulan el envío de correo, que queda para una versión posterior junto con el canal de WhatsApp.
- Los **adjuntos** se guardan en la carpeta local `uploads/`.
- Fuera de alcance de esta demo (quedan para un release posterior): recuperar contraseña (HU-04) y validar con VeriCheck (HU-13).
- Estas cuentas y la contraseña `Demo1234!` son **solo para desarrollo y pruebas**; no deben usarse en producción.
