# Mapa de onboarding — TaskFlow API

Guía breve para ubicarse en el repositorio. Cada hecho cita archivo y línea.
Se separan hechos, inferencias y desconocidos.

## 1. Fuente de verdad del comportamiento

**`docs/contrato-api.md`** — declarado explícitamente como tal.

Hechos:

- `docs/contrato-api.md:3` — "Este documento fija comportamiento observable."
- `docs/contrato-api.md:11-13` — "Los códigos de las tablas siguientes son parte del
  contrato: son lo que afirman los tests, y lo que la sesión 10 compara al revisar. No
  los cambies sin cambiar antes este documento."
- `docs/contrato-api.md:167` — "Los tests pueden incluir casos adicionales. No pueden
  debilitar estas invariantes."
- `README.md:6-7` — "En esta entrega solo existe `GET /health`. El resto del contrato
  se implementa en sesiones posteriores."

Estado actual del código frente al contrato: solo `GET /health` está implementado
(`app/main.py:6-8`), devolviendo `{"status": "ok"}` — coincide con
`docs/contrato-api.md:48-52`.

## 2. Comandos exactos

Todos desde la raíz del repositorio (`README.md:17`).

| Acción | Comando | Fuente |
|---|---|---|
| Instalar | `uv sync --frozen` | `README.md:22` |
| Probar | `uv run pytest -q` | `README.md:28` |
| Revisar estilo | `uv run ruff check .` | `README.md:34` |
| Ejecutar API | `uv run uvicorn app.main:app --reload` | `README.md:50` |
| Verificar salud | `curl http://127.0.0.1:8000/health` | `README.md:56` |
| Levantar PostgreSQL | `docker compose up -d` | `README.md:40` |
| Detener PostgreSQL | `docker compose down` | `README.md:63` |

Hechos de configuración:

- Config de pytest: `asyncio_mode = "auto"`, `testpaths = ["tests"]`
  (`pyproject.toml:20-22`).
- Config de ruff: `target-version = "py312"`, reglas `["E", "F", "I", "UP", "B"]`
  (`pyproject.toml:24-28`). No hay `[tool.ruff.format]` ni comando de formateo
  documentado.
- Entorno verificado en esta máquina: Python 3.12.14, uv 0.12.5, Docker 29.7.2,
  Docker Compose v5.4.0.
- `requires-python = ">=3.12,<3.13"` (`pyproject.toml:6`).

Inferencias:

- No hay comando documentado para "detener la API": se hace con Ctrl-C sobre el
  proceso de uvicorn. El README documenta arrancar pero no detener.

## 3. Motor para los tests de persistencia

**PostgreSQL 18-alpine**, vía `compose.yaml`.

Hechos:

- `compose.yaml:3` — `image: postgres:18-alpine`
- `compose.yaml:5-7` — `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` con
  defaults `taskflow` / `taskflow_local_pw` / `taskflow`
- `compose.yaml:9` — puerto `${POSTGRES_PORT:-5432}:5432`
- `README.md:43-45` — "El servicio `db` (PostgreSQL 18-alpine) queda disponible cuando
  su healthcheck pasa a `healthy`. `compose.yaml` trae valores por defecto locales, así
  que funciona sin `.env`."

El contrato refuerza que la persistencia va sobre esta base y con **migraciones** (no
scripts de init de Docker):

- `docs/contrato-api.md:74-77` — "El curso adopta la migración. Con el script de
  Docker, quien ya tenía el volumen creado nunca recibe el catálogo."
- `docs/contrato-api.md:8` — "IDs enteros positivos generados por la base."
- `docs/contrato-api.md:163` — la matriz de tests exige "Migración desde base vacía y
  rollback de v2."
- `docs/contrato-api.md:79-81` — el seed del catálogo de estados debe ser idempotente.

Inferencia: aún no existe ninguna librería de ORM, driver (`psycopg` / `asyncpg`) ni
herramienta de migración en `pyproject.toml:7-18`.

## 4. Límites sobre archivos con secretos

Hechos:

- `.gitignore:1` — `.env` está ignorado; `git check-ignore` lo confirma
  (`.gitignore:1:.env`).
- `git ls-files` muestra que solo `.env.example` está trackeado, nunca `.env`.
- `.env.example:2` — "Todos los valores de abajo son ficticios y solo sirven para
  desarrollo local."
- El `.env` local actual es una copia de `.env.example`: `POSTGRES_PASSWORD` es el
  default local `taskflow_local_pw`, no un secreto real.
- `docs/contrato-api.md:54` — sobre `/health`: "No expone credenciales ni detalles
  internos."
- `docs/contrato-api.md:14-17` — errores con forma `{"detail": "<mensaje>"}`, mensaje
  legible, sin filtrar internos.

Regla operativa: nunca commitear `.env`; cualquier credencial nueva va a `.env.example`
con valor ficticio y a `.env` local (ignorado).

## 5. Decisiones sin establecer con evidencia (desconocidos)

1. **Herramienta de migración concreta.** El contrato exige migraciones y rollback
   (`docs/contrato-api.md:74`, `:163`) pero no nombra Alembic ni ninguna otra.
   `pyproject.toml` no incluye dependencia de migración.
2. **Driver de base de datos y capa de acceso.** No hay `psycopg` / `asyncpg` /
   SQLAlchemy / SQLModel en `pyproject.toml:7-10`. Sin decidir si el acceso es sync o
   async.
3. **Cómo la app lee la config de conexión.** No existe código que consuma `POSTGRES_*`
   ni una `DATABASE_URL`. `.env.example` solo define variables para Docker Compose, no
   para la app.
4. **Cómo detener la API** de forma documentada (inferencia actual: Ctrl-C).
5. **Comando de formateo de código.** Solo hay `ruff check`; no está definido si se usa
   `ruff format`.
6. **`docs/glosario.md`** — referenciado en `docs/contrato-api.md:79` y `:157`, pero el
   archivo no existe. El término "idempotente" queda sin definición local.
7. **Base de datos para los tests.** Si los tests de persistencia usarán la instancia de
   `compose.yaml`, una base separada, transacciones con rollback o testcontainers. Sin
   evidencia.
8. **Directorio `evidencias/`** está vacío y sin `.gitkeep`; su propósito no está
   documentado.
