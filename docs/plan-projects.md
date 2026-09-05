# Plan: recurso Proyectos

Plan acordado para implementar el recurso `Proyectos` completo (migración, modelo,
esquemas y los cinco endpoints del contrato) en incrementos. Cada incremento es
un commit que se confirma solo; tras terminar uno se para y se espera
aprobación antes del siguiente.

## Fuentes

- `docs/contrato-api.md`: "Convenciones" (códigos HTTP, forma de error, IDs);
  "Orden de las listas" (fila `GET /projects`); sección "Proyectos" (campos y
  tabla de endpoints); "Esquemas de Respuesta" (forma exacta del recurso
  Proyecto); "Matriz Mínima de Tests" (líneas de CRUD de proyectos, IDs
  inexistentes, borrado con tareas, orden estable, esquema exacto).
- `docs/decisiones-ingenieria.md`: "Base de datos" (migraciones con
  `upgrade`/`downgrade` probados en ambos sentidos, tests de persistencia solo
  contra PostgreSQL); "Pruebas" (una capacidad nueva empieza con un test que
  falla por su ausencia; no se debilita un test existente).
- `CLAUDE.md` (raíz del repo): "Fuentes de verdad", "Comandos canónicos",
  "Pruebas", "Persistencia".
- `README.md`: comandos canónicos completos (`uv sync`, `pytest`, `ruff`,
  `docker compose`, `alembic upgrade`/`downgrade`, arranque de la API).
- `docs/plan-persistencia.md` y el historial de commits (`a919e1f`, `4ae37f1`,
  `1aab89d`, `52fd3ac`): decisiones ya tomadas que este plan reutiliza sin
  repetir la discusión (SQLAlchemy 2.x async + asyncpg, Alembic con
  `upgrade`/`downgrade` probados, patrón de migración de tabla).
- Código actual: `app/db.py`, `app/models.py`, `app/schemas.py`, `app/main.py`,
  `tests/conftest.py`, `tests/test_states_endpoint.py`,
  `tests/test_states_migration.py`,
  `alembic/versions/b93548d24a12_*.py` y `bfc6b3db4937_*.py`.

## Fuera de alcance

- Tareas (v1 y v2), sus endpoints, filtros y `due_at`.
- La rama `409` de `DELETE /projects/{id}` cuando el proyecto tiene tareas: el
  contrato la exige, pero la tabla `tasks` no existe todavía en este
  repositorio. Este plan implementa `DELETE` devolviendo `204` siempre que el
  proyecto exista (nunca puede tener tareas todavía); la rama `409` se añade
  cuando se planifique Tareas v1, con acceso real a esa tabla.
- La normalización Unicode de texto de `docs/contrato-api.md` (sección
  "Normalización de texto"): el contrato la limita explícitamente a `title` de
  tarea, no a `name` de proyecto.
- Autenticación, paginación y cualquier metadato de colección: no están en el
  contrato.
- Cambios al contrato o a `docs/decisiones-ingenieria.md`.

## Estado del repositorio al planificar

- `app/main.py`: FastAPI con `GET /health` y `GET /states`; ambos leen la
  sesión de base de datos vía `Depends(get_session)`.
- `app/models.py`: `Base` declarativo y el modelo `State` (catálogo cerrado,
  sembrado por migración). No hay modelo `Project` ni `Task`.
- `app/schemas.py`: solo `StateOut`, con `extra="forbid"` y
  `from_attributes=True`.
- `app/db.py`: engine y `async_sessionmaker` async (SQLAlchemy 2.0.52 +
  asyncpg), leyendo `DATABASE_URL` con fallback derivado de `POSTGRES_*`.
- `alembic/`: dos revisiones. `b93548d24a12` (inicial, sin operaciones de
  esquema) y `bfc6b3db4937` (head actual; crea `states` y siembra el catálogo
  con `INSERT ... ON CONFLICT (code) DO NOTHING`).
- `tests/conftest.py`: fixture `migrated_db` (scope de sesión) que aplica
  `alembic upgrade head` / `downgrade base` una sola vez para toda la sesión de
  tests; fixture `client` que crea un engine nuevo por test y sustituye
  `get_session`, pero **no** aísla transacciones entre tests — hasta ahora
  no hacía falta porque `states` es un catálogo de solo lectura sembrado por
  migración, nunca escrito desde la API.
- `tests/test_states_endpoint.py` y `tests/test_states_migration.py`: únicos
  tests de persistencia existentes; ambos solo leen.
- No existe ningún recurso mutable expuesto por la API todavía. `Proyectos` es
  el primero.

## Decisiones tomadas

**Patrón de migración.** La tabla `projects` se crea por una migración de
Alembic nueva, encadenada tras la head actual (`bfc6b3db4937`), con
`upgrade`/`downgrade` simétricos, siguiendo el mismo patrón que
`alembic/versions/bfc6b3db4937_*.py`. A diferencia de `states`, `projects` no
lleva seed: no es un catálogo cerrado, sus filas las crea la API
(`docs/contrato-api.md`, sección "Proyectos").

**Tipos de columna.** `name` como `sa.String(length=255)` no nulo; `description`
como `sa.Text`, nulable. El contrato no fija una longitud máxima para `name`;
255 es el límite convencional para un campo de texto corto indexable y no
contradice nada del contrato. `description` es texto libre y opcional
("Campos mínimos: `id`, `name`, `description` opcional"), de ahí `Text`
nulable sin límite de longitud.

**Validación de `name`.** Se exige no vacío (`min_length=1`) tanto en la
creación como, si se envía, en la actualización parcial. No se aplica la
normalización Unicode de la sección "Normalización de texto" del contrato,
porque ese texto la limita explícitamente a `title` de tarea; extenderla a
`name` de proyecto sería inventar una regla que el contrato no pide.

**Actualización parcial (`PATCH`).** Se usa `model_dump(exclude_unset=True)`
sobre el esquema de entrada, de modo que un campo ausente en el cuerpo deja el
valor actual intacto y un campo enviado explícitamente como `null` (solo
posible en `description`) lo limpia. Es el idiom estándar de FastAPI/Pydantic
para distinguir "no lo toques" de "bórralo", y es lo que exige una
"actualización parcial" real.

**Aislamiento de tests para datos mutables.** `Proyectos` es el primer recurso
que la API escribe, así que el patrón actual de `tests/conftest.py`
(`migrated_db` de sesión, sin transacción por test) ya no basta: las filas que
crea un test de `POST /projects` quedarían visibles para el siguiente test
dentro de la misma sesión de PostgreSQL, contaminando el orden y el conteo que
`GET /projects` debe verificar como estable. Se cambia la fixture `client` para
que cada test corra dentro de una transacción de PostgreSQL que se revierte al
terminar, usando
`async_sessionmaker(bind=conn, join_transaction_mode="create_savepoint")`
(disponible desde SQLAlchemy 2.0.19; el repo tiene 2.0.52 instalado, confirmado
con `uv run python -c "import sqlalchemy; print(sqlalchemy.__version__)"`).
Esto no toca `migrated_db`, que sigue aplicando el esquema una sola vez por
sesión.

**`DELETE` sin tabla `tasks`.** Ver "Fuera de alcance": se implementa `204`
incondicional (si el proyecto existe) porque no puede haber tareas todavía.

## Incrementos

### Incremento 1 — Migración y modelo de `projects`

- `alembic/versions/<hash>_crea_la_tabla_projects.py` (generado con
  `uv run alembic revision -m "crea la tabla projects"`): crea `projects` con
  `id` (entero, PK), `name` (`String(255)`, no nulo), `description` (`Text`,
  nulo); `downgrade` la elimina. Sin seed.
- `app/models.py`: añade el modelo `Project` (`__tablename__ = "projects"`)
  con las mismas columnas.
- `tests/test_projects_migration.py` (test que falla primero, por ausencia de
  la tabla): tras `migrated_db`, `information_schema.columns` para `projects`
  tiene exactamente `id`, `name`, `description`, con `name` `NOT NULL` y
  `description` nulable; `alembic downgrade -1` deja `to_regclass('public.projects')`
  en `NULL`, y se restaura con `upgrade head` al final del test (mismo patrón
  que `tests/test_states_migration.py::test_downgrade_deja_la_tabla_ausente`).

**Comprobación:**

```bash
docker compose up -d
uv run alembic upgrade head    # aplica también la nueva revisión de projects
uv run pytest -q               # incluye tests/test_projects_migration.py, todo en verde
uv run ruff check .
uv run alembic downgrade base  # revierte ambas revisiones sin error
uv run alembic upgrade head    # deja la base lista para el siguiente incremento
```

### Incremento 2 — Aislamiento de tests mutables, `POST /projects`, `GET /projects`, `GET /projects/{id}`

- `tests/conftest.py`: la fixture `client` abre una transacción por test
  (`conn.begin()`) y la revierte en el `finally`; el `async_sessionmaker` se
  liga a esa conexión con `join_transaction_mode="create_savepoint"`.
- `app/schemas.py`: `ProjectCreate` (`name: str` con `min_length=1`,
  `description: str | None = None`) y `ProjectOut` (`id`, `name`,
  `description`, `extra="forbid"`, `from_attributes=True`).
- `app/main.py`: `POST /projects` (`201`, valida con `ProjectCreate`, devuelve
  `ProjectOut`); `GET /projects` (`200`, `order_by(Project.id)`);
  `GET /projects/{id}` (`200` o `404` con `{"detail": "..."}`).
- `tests/test_projects_endpoint.py` (test que falla primero, por ausencia de
  las rutas):
  - `POST /projects` con `name` y sin `description` → `201`, cuerpo
    `{"id", "name", "description": null}`, sin campos de más.
  - `POST /projects` con `name` vacío → `422`.
  - Crear varios proyectos y `GET /projects` dos veces → misma lista, mismos
    ids en el mismo orden ascendente por `id`.
  - `GET /projects/{id}` de uno recién creado → `200` con el mismo cuerpo que
    devolvió el `POST`.
  - `GET /projects/999999` → `404`, `{"detail": "..."}`.

**Comprobación:**

```bash
uv run pytest -q      # tests/test_projects_endpoint.py y el resto, todo en verde
uv run ruff check .
```

### Incremento 3 — `PATCH /projects/{id}`

- `app/schemas.py`: `ProjectUpdate` (`name: str | None = None` con
  `min_length=1` cuando se envía; `description: str | None = None`).
- `app/main.py`: `PATCH /projects/{id}` — `404` si no existe; aplica
  `model_dump(exclude_unset=True)` sobre `ProjectUpdate` y actualiza solo los
  campos presentes; `200` con el recurso actualizado.
- `tests/test_projects_endpoint.py`, casos nuevos:
  - `PATCH` solo `name` → cambia `name`, conserva `description`.
  - `PATCH` con `{"description": null}` explícito → limpia `description`
    (queda `null`), conserva `name`.
  - `PATCH` con `{"name": ""}` → `422`.
  - `PATCH /projects/999999` → `404`.

**Comprobación:**

```bash
uv run pytest -q
uv run ruff check .
```

### Incremento 4 — `DELETE /projects/{id}`

- `app/main.py`: `DELETE /projects/{id}` — `404` si no existe; si existe, lo
  borra y devuelve `204` sin cuerpo (ver "Fuera de alcance": sin comprobación
  de tareas, porque `tasks` no existe todavía).
- `tests/test_projects_endpoint.py`, casos nuevos:
  - `DELETE` de un proyecto existente → `204`, cuerpo vacío; `GET` posterior al
    mismo id → `404`.
  - `DELETE /projects/999999` → `404`.

**Comprobación:**

```bash
uv run pytest -q      # matriz completa de Proyectos en verde
uv run ruff check .
```
