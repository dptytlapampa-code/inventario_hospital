# Inventario Hospitalario

Sistema web completo y listo para producción para la gestión de inventario hospitalario y técnico en hospitales públicos (Hospital Dr. Lucio Molas y Hospital René Favaloro), con autenticación y permisos granulares, licencias/vacaciones (con workflow de aprobación por Superadmin y reemplazos), actas PDF, adjuntos, insumos/componentes con stock, auditoría, buscador global y dashboard con Chart.js.

## Windows 11 – Arranque rápido

1. **Doble clic en `scripts/bootstrap.bat` y seguí los prompts.** No hace falta abrir PowerShell manualmente; el `.bat` ejecuta el flujo completo con `-ExecutionPolicy Bypass`.
2. **¿Qué hace el script automáticamente?**
   - Detecta la raíz del proyecto aunque la ruta contenga espacios.
   - Verifica que exista Python 3.11+ y muestra un enlace de descarga si falta.
   - Crea y activa `.venv` (si ya existe lo reutiliza) y usa siempre `.\.venv\Scripts\python.exe -m pip ...`.
   - Actualiza `pip`, instala `requirements.txt` y, si `psycopg2` falla, instala `psycopg2-binary` como fallback.
   - Crea `.env` cuando falta solicitando los datos por `Read-Host` y muestra los valores existentes cuando ya está configurado.
   - Valida la conexión a PostgreSQL con `psycopg2`, ofrece crear la base si no existe y detiene el proceso con mensajes claros ante errores.
   - Ejecuta `python -m flask db heads`, mergea múltiples heads si es necesario y aplica `python -m flask db upgrade`.
   - Corre `python -m seeds.seed` (idempotente) para poblar usuarios, hospitales, etc.
   - Lanza `python -m flask run --host=127.0.0.1 --port=5000 --debug` y abre el navegador en `http://127.0.0.1:5000`.
3. **Valores por defecto de `.env` (enter para aceptar):**
   - Host: `localhost`
   - Base de datos: `inventario_hospital`
   - Usuario: `salud`
   - Password: `Catrilo.20`
   - El script genera además `FLASK_APP=wsgi.py` y `FLASK_ENV=development`.
   - Podés editar `.env` manualmente o borrar el archivo y volver a ejecutar el bootstrap para reconfigurar.
4. **Primer usuario disponible después del seed:** `admin / 123456` (Superadmin).
5. **Rearranque rápido:** una vez provisionado, usá `scripts/run_server.ps1` para iniciar solo el servidor (activa `.venv`, lee `.env`, valida PostgreSQL y ejecuta `python -m flask run --debug`).

## Tabla de contenido

0. [Windows 11 – Arranque rápido](#windows-11--arranque-rápido)
1. Objetivos
2. Alcance funcional
3. Stack técnico
4. Estructura del repositorio
5. Instalación y ejecución
   - [5.1 Variables de entorno](#51-variables-de-entorno)
   - [5.2 Sin Docker](#52-sin-docker)
   - [5.3 Con Docker](#53-con-docker)
   - [5.4 Makefile (atajos)](#54-makefile-atajos)
6. Base de datos, migraciones y seeds
   - [6.1 Primer arranque / SQLite](#61-primer-arranque--sqlite)
7. Roles, permisos y seguridad
8. Módulo de Licencias/Vacaciones
   - [8.1 Modelo de datos](#81-modelo-de-datos)
   - [8.2 Reglas de negocio](#82-reglas-de-negocio)
   - [8.3 UI y flujos](#83-ui-y-flujos)
   - [8.4 Integración con seguridad](#84-integración-con-seguridad)
9. Gestión de equipos, insumos y actas
10. Auditoría y reportes
11. Checklist de seguridad antes de producción
12. Testing
13. Uso con GitHub y Codex (desarrollo por partes)
14. Troubleshooting
15. Licencia y autoría

## 1. Objetivos

- Centralizar el inventario tecnológico (impresoras, routers, notebooks, etc.) por Hospital → Servicio → Oficina.
- Gestionar movimientos, reparaciones, altas/bajas, historial por equipo y asignación de insumos.
- Permisos granulares por hospital y por módulo (definidos por Superadmin).
- Licencias/vacaciones para Admins y Técnicos con aprobación del Superadmin y reemplazos temporales.
- Generar actas PDF (entrega/préstamo/transferencia) y adjuntar documentos.
- Auditar acciones y visualizar métricas en dashboard (Chart.js).
- Proveer instalación reproducible (Docker Compose opcional) y buenas prácticas de seguridad.

## 2. Alcance funcional

- Autenticación y roles: Superadmin, Admin, Técnico y Lectura. Usuario inicial: `admin / 123456` (Superadmin). Otros usuarios de ejemplo se crean con `flask demo-seed --force`.
- Permisos granulares por hospital y módulo (inventario, insumos, actas, adjuntos, docscan, reportes, auditoría, licencias).
- Ubicaciones jerárquicas: Hospital → Servicio → Oficina (ABM, validaciones de duplicados, edición sin cambiar IDs).
- Equipos: tipos predefinidos, estados (Operativo, En Servicio Técnico, De baja), expediente/año opcionales, historial.
- Insumos y componentes: stock, número de serie (o “sin número visible” con ID ficticio), asignaciones y entregas directas.
- Actas PDF: entrega/préstamo/transferencia; quedan registradas en el historial del/los equipo/s.
- Adjuntos: PDF/JPG/PNG tipados (factura, presupuesto, acta, planilla patrimonial, otros).
- Docscan: módulo independiente para documentación escaneada (tipos de nota configurables por Superadmin).
- Licencias/vacaciones: workflow de aprobación por Superadmin, reemplazos y bloqueo operativo por período.
- Buscador global y dashboard con KPIs.
- Auditoría completa de acciones relevantes.

## 3. Stack técnico

- **Backend:** Python 3.11+, Flask (Blueprints, Jinja2), Flask-Login, Flask-Migrate (Alembic), SQLAlchemy, WTForms.
- **DB:** SQLite (auto en desarrollo) o PostgreSQL configurado vía `SQLALCHEMY_DATABASE_URI`.
- **Frontend:** HTML5, CSS3, Bootstrap 5, JavaScript (vanilla), Chart.js.
- **PDF:** WeasyPrint o ReportLab (configurar dependencias del SO si corresponde).
- **QR:** `qrcode` (por equipo).
- **Testing:** pytest.
- **Automación:** Makefile (instalación, migraciones, run, tests).
- **Docker (opcional):** docker-compose para app + Postgres.

## 4. Estructura del repositorio

```
inventario_hospitalario/
├─ app/
│  ├─ __init__.py
│  ├─ extensions.py              # db, migrate, login_manager, csrf, bcrypt, logging
│  ├─ security/
│  │  ├─ decorators.py           # @login_required, @require_role, @require_permission, @require_hospital_access
│  │  └─ policy.py               # matriz de permisos por módulo y hospital
│  ├─ models/
│  │  ├─ base.py
│  │  ├─ usuario.py              # estados (activo/suspendido por licencia), rol, hash de contraseña
│  │  ├─ rol.py                  # Superadmin, Admin, Técnico
│  │  ├─ permisos.py             # permisos por módulo y hospital (many-to-many con atributos)
│  │  ├─ hospital.py             # Hospital, Servicio, Oficina
│  │  ├─ equipo.py               # tipos predefinidos, estados, historial
│  │  ├─ insumo.py               # stock y asignaciones
│  │  ├─ acta.py                 # actas PDF y sus items
│  │  ├─ adjunto.py              # documentos adjuntos por equipo
│  │  ├─ docscan.py              # documentación escaneada (PDF/JPG) con tipos
│  │  ├─ licencia.py             # licencias/vacaciones + workflow
│  │  ├─ auditoria.py            # log de acciones
│  │  └─ __init__.py
│  ├─ forms/
│  │  ├─ auth.py, hospital.py, equipo.py, insumo.py, acta.py, docscan.py, adjunto.py, permisos.py, licencia.py
│  ├─ services/
│  │  ├─ pdf_service.py, qr_service.py, search_service.py, audit_service.py, licencia_service.py
│  ├─ routes/
│  │  ├─ auth/, main/, ubicaciones/, equipos/, insumos/, actas/, adjuntos/, docscan/, permisos/, licencias/
│  ├─ templates/
│  │  ├─ layout.html, base_nav.html, main/dashboard.html, main/busqueda.html, licencias/...
│  ├─ static/
│  │  ├─ css/custom.css, js/dashboard.js, js/buscador.js, js/licencias_cal.js
│  └─ utils/
│     ├─ dates.py, files.py
├─ migrations/
├─ seeds/
│  ├─ seed.py
│  └─ fixtures/
├─ tests/
│  ├─ conftest.py, test_auth.py, test_permisos.py, test_ubicaciones.py, test_equipos.py, test_licencias.py
├─ .env.example
├─ config.py
├─ wsgi.py (o run.py)
├─ Makefile
├─ requirements.txt
├─ docker-compose.yml (opcional)
├─ Dockerfile (opcional)
└─ README.md
```

## 5. Instalación y ejecución

### 5.1 Variables de entorno

Copia `.env.example` a `.env` y ajusta valores:

```
FLASK_APP=wsgi.py
FLASK_ENV=development
FLASK_RUN_HOST=0.0.0.0
FLASK_RUN_PORT=5000
SECRET_KEY=change_me
# Si se deja vacío, por defecto SQLite para desarrollo:
# SQLALCHEMY_DATABASE_URI=postgresql://usuario:pass@localhost/inventario_hospital
AUTO_SEED_ON_START=1
DEMO_SEED_VERBOSE=1
UPLOAD_FOLDER=./uploads
DOCSCAN_FOLDER=./uploads/docscan
DEFAULT_PAGE_SIZE=20
LOG_LEVEL=INFO
```

### 5.2 Sin Docker

```
# 1) venv e instalar deps
py -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt

# 2) (opcional) .env para Postgres; si no, usa SQLite inventario.db por defecto
copy .env.example .env
# editar SQLALCHEMY_DATABASE_URI si querés Postgres
# dejar AUTO_SEED_ON_START=1 para cargar datos demo en el primer arranque

# 3) Migraciones (si hay carpeta migrations)
set FLASK_APP=wsgi.py           # (PowerShell: $env:FLASK_APP="wsgi.py")
flask db upgrade

# 4) Arrancar (carga auto-seed si la base está vacía y AUTO_SEED_ON_START=1)
flask run --host=127.0.0.1 --port=5000 --debug

# 5) (opcional) Forzar demo seed manual
flask demo-seed --force
```

> Para Linux/macOS usá `python3 -m venv .venv`, `source .venv/bin/activate`, `cp .env.example .env` y los equivalentes para `export`.

### 5.3 Con Docker

Requiere Docker y Docker Compose.

```
docker compose up --build -d
docker compose logs -f
```

La app quedará disponible en `http://localhost:8000`.
La base apunta a `postgresql://salud:Catrilo.20@db:5432/inventario_hospital`.

### 5.4 Makefile (atajos)

```
make install   # instala deps en .venv
make run       # python wsgi.py
make test      # pytest
# (si agregaste helpers Docker)
make up        # docker compose up -d
make down      # docker compose down
make migrate   # docker compose exec app flask db migrate -m "auto"
make upgrade   # docker compose exec app flask db upgrade
```

## 6. Base de datos, migraciones y seeds

ORM: SQLAlchemy + Flask-Migrate (Alembic).

Crear/actualizar esquema:

```
flask db migrate -m "cambio X"
flask db upgrade
```

El repositorio incluye una migración inicial con todas las tablas declaradas en `app/models`. El comando `flask dbsafe-upgrade` toma la URI configurada en `SQLALCHEMY_DATABASE_URI`, detecta múltiples heads de Alembic, realiza un merge automático si es necesario y deja la base migrada.

Seeds (`flask demo-seed` o auto-seed en desarrollo): reutiliza la aplicación Flask (misma configuración `.env`), verifica la conexión configurada (SQLite o PostgreSQL) y carga los catálogos de manera idempotente:

- `admin / 123456` (Superadmin global)
- `admin_molas / Cambiar123!` y `admin_favaloro / Cambiar123!` (Admins locales)
- `tecnico_molas / Cambiar123!` y `tecnico_favaloro / Cambiar123!` (Técnicos por hospital)
- `consulta / Cambiar123!` (Usuario de solo lectura)
- Equipos/insumos/actas/adjuntos/licencias de ejemplo
- Permisos por hospital y módulo listos para operar.

### 6.1 Primer arranque

En desarrollo, si no configurás `SQLALCHEMY_DATABASE_URI`, el proyecto crea `inventario.db` (SQLite) junto al código y ejecuta el seed automáticamente en el primer `flask run` cuando `AUTO_SEED_ON_START=1`. Para usar PostgreSQL definí la URI correspondiente antes de correr las migraciones (`flask db upgrade`) o ejecutar `flask demo-seed`.

## 7. Roles, permisos y seguridad

- **Roles:** Superadmin (gestión completa), Admin (operativa local por hospital), Técnico (operativa limitada).
- **Permisos granulares** por hospital y módulo: definidos en UI de Superadmin.
- **Decorators:**
  - `@require_role(...)`
  - `@require_permission('<modulo>')`
  - `@require_hospital_access(hospital_id)`
- **Estados de usuario:** activo / suspendido por licencia (ver módulo de licencias).
- **Passwords:** si no se instala `flask-bcrypt` el sistema cae en una implementación PBKDF2 segura integrada (útil para entornos sin acceso a PyPI).

## 8. Módulo de Licencias/Vacaciones

### 8.1 Modelo de datos

Entidad `Licencia`:

- `usuario_id`, `hospital_id` (opcional)
- `tipo` (Vacaciones, Enfermedad, Estudio, Asuntos Particulares, Maternidad/Paternidad, Capacitación, Otro)
- `fecha_inicio`, `fecha_fin`, `dias_habiles`
- `estado` (Borrador, Pendiente, Aprobada, Rechazada, Cancelada)
- `comentario_solicitante`, `comentario_superadmin`
- `requires_replacement`, `replacement_user_id` (validado)
- Índices por usuario, `fecha_inicio` y `estado`

### 8.2 Reglas de negocio

- **Solicitud:** Admin/Técnico crea en Borrador y envía a Pendiente. Validación de fechas y solapamientos. Cálculo de días hábiles (excluye fines de semana).
- **Aprobación Superadmin:** aprueba/rechaza con comentario; si `requires_replacement`, debe asignarse reemplazo con permisos equivalentes y sin conflicto de fechas.
- **Efectos operativos:**
  - Vigencia de licencia Aprobada → usuario suspendido por licencia (bloqueo de login o bloqueo modular por hospital/módulos; estrategia documentada).
  - Fin de licencia → revertir a activo (al evaluar permisos o job simple).
- **Reemplazos:** permisos temporales equivalentes al reemplazante por el período; alta/baja registrada en auditoría.
- **Calendario:** vista mensual/semanal (JS simple), con Aprobadas y Pendientes; exportación CSV.

### 8.3 UI y flujos

- **Solicitar:** tipo, rango de fechas, comentario, `requires_replacement` y (si aplica) `replacement_user_id`.
- **Mis solicitudes:** estados, fechas, días hábiles, hospital, reemplazo, acciones.
- **Aprobar (Superadmin):** filtros + detalle; acciones de aprobar/rechazar; logs de auditoría.
- **Calendario y Detalle** con trail de auditoría.

### 8.4 Integración con seguridad

- `decorators.py`: bloquea login o acceso modular durante la vigencia (según estrategia elegida).
- `policy.py`: aplica permisos temporales por reemplazo.

## 9. Gestión de equipos, insumos y actas

**Equipos:**

- Tipos predefinidos: Impresora, Router, Switch, Notebook, CPU, Monitor, Access Point, Scanner, Proyector, Teléfono IP, UPS, Otro.
- Estados: Operativo (verde), En Servicio Técnico (amarillo), De baja (rojo).
- Reglas: Mantenimiento “Servicio Externo” → En Servicio Técnico; Alta técnica → Operativo (registrar desde/hasta y duración); “Dar de baja” → De baja + reporte.

**Insumos/Componentes:**

- Stock, número de serie obligatorio o “sin número visible” (ID ficticio).
- Asignación a equipos o entregas directas; descuenta stock y registra en historial/auditoría.

**Actas PDF:**

- Entrega/préstamo/transferencia; incluye equipos, marcas/modelos/serie y accesorios.
- Trae hospital, servicio, oficina, fecha, receptor y usuario que generó la acción.
- Queda en historial de cada equipo.

## 10. Auditoría y reportes

- **Auditoría:** altas/ediciones/bajas, cambios de estado, generación/descarga de PDFs, asignación de insumos, cambios de permisos, aprobaciones/rechazos de licencias, inicios de sesión, etc.
- **Reportes/Chart.js:** KPIs (equipos por estado/tipo, por hospital/servicio, insumos críticos, tiempos promedio de servicio técnico, etc.).
- **Buscador global:** serie, MAC, bien patrimonial, responsable, modelo, expediente, etc., con filtros y paginación.

## 11. Checklist de seguridad antes de producción

1. Rotar `SECRET_KEY` y variables sensibles (usar `.env` fuera del repo).
2. Asegurar HTTPS detrás de un proxy/Nginx.
3. Limitar tamaño y tipos de archivos en uploads; validar nombres y rutas no ejecutables.
4. Revisar CSRF activo en formularios; validar inputs en servidor.
5. Revisar permisos por módulo/hospital y decorators en todas las vistas.
6. Activar logging con rotación; nivel INFO/WARNING en prod.
7. Revisar roles y seeds: cambiar contraseña del admin.
8. Habilitar backups de PostgreSQL (`pg_dump`, `pg_restore`).
9. (Opcional) Rate limiting para login/acciones sensibles.
10. Revisar dependencias de PDF (WeasyPrint/ReportLab) y paquetes del sistema.

## 12. Testing

Unit/Integration con pytest:

```
pytest -q
```

Casos clave:

- Autenticación y permisos por hospital/módulo.
- ABM de ubicaciones y equipos.
- Reglas de servicio técnico y alta técnica.
- Licencias (solapamientos, estados, bloqueos operativos, reemplazos).
- Generación de actas PDF (smoke test de servicio).
- Auditoría.

### 12.1 Pruebas manuales sugeridas

1. Crear/editar un equipo verificando que los selectores Hospital → Servicio → Oficina respeten la dependencia y permitan buscar toda la base desde el botón “…” (enviar `q=...`).
2. Marcar “Sin N° de serie visible” y confirmar que el sistema deshabilita el campo y genera un código interno `EQ-AAAAMMDD-####` al guardar.
3. Subir y eliminar evidencias (PNG/JPG/PDF) verificando tamaño máximo, vista previa y confirmando que la eliminación solicita CSRF y registra evento en el historial.
4. Revisar el detalle del equipo: los bloques “Historial reciente” y “Actas vinculadas” deben mostrar hasta tres ítems y ofrecer el enlace “Ver todo” para abrir la vista completa con filtros.
5. Actualizar datos personales desde “Mi perfil” y confirmar que el dropdown superior muestra el acceso rápido junto con la opción para cerrar sesión.

## 13. Uso con GitHub y Codex (desarrollo por partes)

- GitHub aloja el repositorio (rama `main`).
- Codex crea PRs iterativos (p. ej., PR 1: base; PR 2: modelos; PR 3: licencias; PR 4: auth; …).

**Flujo recomendado:**

1. Conectar ChatGPT ↔ GitHub y autorizar el repo.
2. En Codex, pedir features concretas (con este README como hoja de ruta).
3. Revisar y mergear PRs en `main`.
4. Desplegar con Docker en tu Ubuntu Server (VMware) o en tu entorno local.

## 14. Troubleshooting

- **psycopg2 o conexión fallida:** verificar `SQLALCHEMY_DATABASE_URI`, credenciales y que Postgres esté levantado.
- **Migraciones:**
  - Con el repositorio tal como viene alcanza con `flask dbsafe-upgrade`.
  - Si creás nuevas migraciones desde cero: `flask db init` → `flask db migrate` → `flask dbsafe-upgrade`.
  - Error de heads múltiples: `flask dbsafe-upgrade` realiza el merge automático y luego aplica `upgrade`.
- **WeasyPrint/ReportLab:** pueden requerir paquetes del SO (Cairo, Pango, libffi, etc.). Agregarlos en Dockerfile o instalar en el host.
- **Docker puerto ocupado:** cambia mapeo (`8000:8000` → `8080:8000`) en `docker-compose.yml`.
- **Subidas de archivos:** revisar `UPLOAD_FOLDER`, permisos de carpeta y `MAX_CONTENT_LENGTH`.

## 15. Licencia y autoría

- **Autor:** Pla Cárdenas, Facundo
- **Propósito:** sistema de inventario hospitalario, con licencias y permisos granulares por hospital/módulo.
- **Licencia:** define la licencia de tu preferencia para el repositorio (MIT/Apache-2.0/AGPL, etc.).

