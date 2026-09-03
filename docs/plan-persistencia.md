# Plan: conexión de la API a PostgreSQL

Plan acordado para conectar la API a PostgreSQL en incrementos. Solo cubre
**Salud** y **Estados**. Cada incremento es un commit que se confirma solo; tras
terminar uno se para y se espera aprobación antes del siguiente.

Fuentes: `docs/contrato-api.md` (secciones Salud y Estados),
`docs/decisiones-ingenieria.md`, `CLAUDE.md`.

## Fuera de alcance

Proyectos, tareas, filtros, `due_at`, skills, hooks y CI.

## Estado del repositorio al planificar

- `app/main.py`: FastAPI con un solo endpoint, `GET /health` -> `200 {"status": "ok"}`.
- Sin ORM, sin driver de PostgreSQL, sin Alembic, sin código que lea configuración
  de conexión.
- `tests/test_health.py`: un test async (sin decorador, `asyncio_mode = "auto"`),
  app en memoria vía `httpx.ASGITransport`.
- `pyproject.toml`: deps `fastapi`, `uvicorn`; dev `pytest`, `pytest-asyncio`,
  `httpx`, `ruff`. Python 3.12.x. Ruff con reglas `E, F, I, UP, B`.
- `compose.yaml`: servicio `db` PostgreSQL 18-alpine, healthcheck, defaults
  locales, puerto `5432`. Funciona sin `.env`.
- `.env.example`: solo variables `POSTGRES_*` para Compose. No hay `DATABASE_URL`.
- `docs/decisiones-ingenieria.md` nombra Alembic con `upgrade`/`downgrade`
  probados en ambos sentidos; tests de persistencia contra PostgreSQL, nunca
  SQLite; capacidad nueva empieza con test que falla.

## Decisiones tomadas

Driver y capa de acceso: acceso **async** con SQLAlchemy 2.x y `asyncpg`. Se
aplica desde el incremento 1.

Por qué encaja con lo que ya existe: la app FastAPI y el único test
(`tests/test_health.py`, async sin decorador con `asyncio_mode = "auto"` y
`httpx.ASGITransport`) ya son async, así que una capa de acceso async no
introduce un modelo de ejecución distinto al del repositorio.

## Incrementos

### Incremento 1 - Cableado de dependencias y configuración de conexión

- Añadir a `pyproject.toml`: `sqlalchemy[asyncio]`, `asyncpg`, `alembic`.
- Módulo `app/db.py`: crea el `async_engine` y `async_sessionmaker` leyendo
  `DATABASE_URL` del entorno.
- Añadir `DATABASE_URL` a `.env.example` con valor ficticio local derivable de
  los `POSTGRES_*` ya presentes.
- **Comprobación:** `uv sync` resuelve; `uv run python -c "from app.db import engine"`
  importa sin conectar; `uv run pytest -q` y `uv run ruff check .` siguen verdes
  (el test de health no toca la base).

### Incremento 2 - Alembic inicializado, sin cambios de esquema todavía

- `alembic init`, ajustar `env.py` para usar `DATABASE_URL` y el metadata de la
  app, revisión inicial sin operaciones de esquema.
- Documentar en `README.md` los comandos `uv run alembic upgrade head` /
  `downgrade base`.
- **Comprobación:** con `docker compose up -d`, `uv run alembic upgrade head` crea
  `alembic_version`; `uv run alembic downgrade base` la revierte; `alembic current`
  refleja el estado. Ambos sentidos probados.

### Incremento 3 - Migración de la tabla `states` con seed idempotente

- Migración Alembic que crea la tabla del catálogo (`id`, `code`, campo de orden)
  y hace el seed de los cuatro estados (`PENDIENTE`, `EN_CURSO`, `BLOQUEADA`,
  `HECHA`) en `upgrade`; `downgrade` la elimina.
- Seed idempotente: `INSERT ... ON CONFLICT DO NOTHING` sobre `code` único, de
  modo que `upgrade` dos veces (o sobre base ya poblada) no duplica.
- **Comprobación:** test de persistencia contra PostgreSQL (primer test que
  necesita la base) que: (a) tras `upgrade head` hay exactamente 4 estados con
  los códigos del contrato; (b) re-ejecutar el seed no cambia el conteo;
  (c) `downgrade` deja la tabla ausente. Aquí se decide y documenta la estrategia
  de base de tests.

### Incremento 4 - Endpoint `GET /states`

- Test que falla primero: `GET /states` -> `200`, lista JSON en la raíz, cada
  elemento exactamente `{"id", "code"}`, orden por campo de catálogo con `id` de
  desempate.
- Implementación: ruta que consulta la tabla y serializa con un esquema Pydantic
  de salida estricto (sin campos de más).
- **Comprobación:** el nuevo test pasa; el de health sigue pasando; `ruff` verde.
  Dos llamadas idénticas devuelven los `id` en la misma posición.
