# Tech Solutions – Sistema de gestión de servicios

Trabajo práctico de **Análisis y Metodología de Sistemas** – Escuela Da Vinci.
Equipo **"Las Cloves"**: Brian Lopez, Franco Di Giovanni, Abril Gullotta, Aristides Azocar y Valentina Quiroga.

Aplicación web en **Python + Flask**, construida sobre la base FlyFlask, para la Consultora Tech Solutions.

## Ramas

| Rama | Uso |
|---|---|
| `main` | Versión entregable. Recibe cambios solo al cerrar cada bloque (tags `v1-bloque1`, `v2-bloque2`…). |
| `develop` | Integración. Rama por defecto: todos los pull requests van acá. |
| `base/flyflask` | Adaptación inicial de FlyFlask (se hace una sola vez, antes del Bloque 1). |
| `feature/HU-XX-nombre` | Una rama por historia de usuario. Ej.: `feature/HU-08-registrar-solicitud`. |
| `fix/descripcion` | Corrección de errores o cambios en los modelos. |
| `docs/descripcion` | Documentación. Ej.: `docs/HU-25-tutorial`. |

Nadie sube cambios directo a `main` ni a `develop`: todo entra por **pull request** con la aprobación de otro integrante (es la columna *Code Review / QA* del Kanban).

## Flujo de trabajo por historia

```bash
git checkout develop
git pull origin develop
git checkout -b feature/HU-08-registrar-solicitud
# ...trabajo...
git commit -m "HU-08: alta de solicitud en estado pendiente"
git push -u origin feature/HU-08-registrar-solicitud
```

Después se abre el pull request hacia `develop`, con el link a la tarjeta de Trello y los criterios de aceptación probados.

## Archivos compartidos: una sección por persona

Para no pisarnos al hacer merge, estos archivos tienen una sección marcada con el nombre de
cada integrante. **Cada uno agrega sus líneas solo dentro de su sección**:

- `app.py`: imports y registro de blueprints.
- `models.py`: constantes y modelos nuevos, al final del archivo.
- `seed.py`: datos de prueba, dentro de `run_seed()`.
- `templates/panel.html`: accesos del cliente.
- `templates/admin/dashboard.html`: accesos de administración.

Reglas: no tocar `templates/base.html`; el código nuevo va en su propia carpeta y blueprint;
si cambiás una columna de un modelo que ya existe, avisá al grupo (todos borran
`instance\techsolutions.db`); antes del PR, `git merge origin/develop`.

## Bloques

| Bloque | Historias |
|---|---|
| 1 – Demo MVP | HU-02, HU-06, HU-08, HU-11, HU-14, HU-15, HU-25 |
| 2 – Cliente | HU-01, HU-03, HU-05, HU-07, HU-09, HU-10 |
| 3 – Administración | HU-16, HU-17, HU-18, HU-19, HU-20, HU-23 |
| 4 – Integraciones y reportes | HU-12, HU-21, HU-22, HU-24 |
| Release posterior | HU-04, HU-13, canal WhatsApp de HU-07 |

## Cómo ejecutar el proyecto

*(Se completa con el tutorial de HU-25 cuando esté lista la base.)*
