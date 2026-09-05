# Plan: recurso Tareas (v1 y v2 completas)

Plan acordado para implementar el recurso `Tareas` completo: los cinco
endpoints de Tareas v1, el campo `due_at` y el filtro `overdue` de Tareas v2, y
el cierre del `409` de `DELETE /projects/{id}` que quedó pendiente en
`docs/plan-projects.md`. Cada incremento es un commit que se confirma solo;
tras terminar uno se para y se espera aprobación antes del siguiente.

## Fuentes

- `docs/contrato-api.md`: "Convenciones" (códigos HTTP, forma de error, IDs,
  "una referencia a proyecto o estado inexistente no se crea implícitamente");
  "Normalización de texto" (algoritmo exacto para `title`); "Orden de las
  listas" (fila `GET /tasks`); sección "Tareas v1" (campos y tabla de
  endpoints); sección "Tareas v2: Fechas Límite" (`due_at`, `overdue`, fuera de
  alcance de v2); "Esquemas de Respuesta" (forma exacta de Tarea, con y sin
  `due_at`); "Matriz Mínima de Tests".
- `docs/decisiones-ingenieria.md`: "Base de datos" (migraciones con
  `upgrade`/`downgrade` probados en ambos sentidos, tests de persistencia solo
  contra PostgreSQL); "Pruebas" (una capacidad nueva empieza con un test que
  falla por su ausencia; no se debilita un test existente).
- `CLAUDE.md` (raíz del repo): "Fuentes de verdad", "Comandos canónicos",
  "Pruebas", "Persistencia".
- `README.md`: comandos canónicos completos.
- `docs/plan-projects.md`: "Fuera de alcance" — deja escrito que el `409` de
  `DELETE /projects/{id}` "se añade cuando se planifique Tareas v1, con acceso
  real a esa tabla". Ese momento es este plan.
- Código actual: `app/models.py`, `app/schemas.py`, `app/main.py`,
  `tests/conftest.py`, `tests/test_projects_endpoint.py`,
  `tests/test_projects_migration.py`, `tests/test_states_migration.py`,
  `alembic/versions/*.py`.

## Fuera de alcance

- Recordatorios, scheduler, zona horaria preferida del usuario y cambio
  automático de estado: el propio contrato los declara fuera de alcance de
  Tareas v2.
- La batería de regresión exhaustiva de caracteres Unicode invisibles en
  `title` (p. ej. `U+200B`): el contrato ya fija el algoritmo completo (que
  este plan implementa tal cual, sin una versión parcial), pero
  `docs/contrato-api.md` reserva esa batería de regresión para la sesión 7
  ("la sesión 7 trabaja este defecto a fondo"; "Matriz Mínima de Tests": "los
  invisibles Unicode se trabajan como regresión en la sesión 7"). Este plan
  prueba solo lo que la matriz pide ahora: título vacío y espacios ASCII.
- Paginación o metadatos de colección en `GET /tasks`: no están en el
  contrato.
- Relaciones ORM (`relationship()`) entre `Task`, `Project` y `State`: los
  esquemas de salida solo necesitan `project_id`/`state_id` escalares: no hace
  falta cargar objetos relacionados.
- Endpoints nuevos para `states`: el catálogo sigue sin crearse ni borrarse
  desde la API.
- Cambios a `docs/contrato-api.md` o `docs/decisiones-ingenieria.md`.

## Estado del repositorio al planificar

- `app/models.py`: `Base`, `State` (catálogo cerrado) y `Project` (`id`,
  `name` `String(255)` no nulo, `description` `Text` nulo). Sin modelo `Task`.
- `app/schemas.py`: `StateOut`; `ProjectCreate`/`ProjectUpdate` (`name` con
  `min_length=1`, `description` opcional) y `ProjectOut` (`extra="forbid"`,
  `from_attributes=True`). Sin esquemas de Tarea.
- `app/main.py`: `GET /health`, `GET /states`, y los cinco verbos de
  `/projects`. `delete_project` (línea 73-81) borra sin comprobar tareas
  asociadas, con un comentario explícito que remite a
  `docs/plan-projects.md`, "Fuera de alcance".
- `alembic/`: tres revisiones encadenadas —
  `b93548d24a12` (inicial) → `bfc6b3db4937` (`states`, con seed) →
  `da291a58134e` (`projects`, sin seed, cabeza actual). Ninguna toca `tasks`.
- `tests/conftest.py`: fixture `migrated_db` (scope de sesión, aplica
  `upgrade head` / `downgrade base`) y fixture `client`, que desde el trabajo
  de Proyectos aísla cada test en una transacción de PostgreSQL revertida
  (`join_transaction_mode="create_savepoint"`). Sirve tal cual para Tareas:
  no hace falta tocar este archivo.
- `tests/test_states_migration.py`: ya corrige el patrón de referirse a una
  revisión exacta (`_states_revision_module().down_revision`) en vez de un
  offset relativo `"-1"`, tras la fragilidad que expuso apilar la migración de
  `projects` encima de la de `states`.
- No existe ningún archivo de tests de Tareas.

## Decisiones tomadas

**Dos migraciones, no una.** `tasks` v1 (sin `due_at`) y la adición de
`due_at` en v2 son dos migraciones de Alembic encadenadas, igual que
`states`/`projects` son migraciones separadas. Justificación: la "Matriz
Mínima de Tests" exige explícitamente "migración desde base vacía y rollback
de v2", lo que solo tiene sentido si v2 es una revisión propia que se puede
revertir de forma independiente de la tabla base.

**Referencia a revisión exacta en los tests de migración de Tareas, no
offset relativo.** Ambas migraciones de Tareas (v1 y v2) prueban su
`downgrade` apuntando al `down_revision` real de la migración bajo prueba
(mismo patrón que la corrección ya aplicada en
`tests/test_states_migration.py`), no a `"-1"`. Justificación: `"-1"` ya
demostró ser frágil en este repositorio en cuanto se apiló una revisión
nueva encima.

**Tipos de columna.** `title` como `sa.String(length=255)` no nulo (mismo
límite que `Project.name`, por la misma razón: texto corto sin límite fijado
por el contrato); `description` como `sa.Text` nulo (mismo patrón que
`Project.description`); `project_id` y `state_id` como `sa.Integer` no nulos
con `ForeignKey`, sin `ondelete` en cascada (el contrato ya establece, para
Proyectos, que "no hay borrado en cascada implícito"; se extiende el mismo
principio a las referencias de Tareas). `due_at` (v2) como
`sa.DateTime(timezone=True)`, nulo.

**Validación de existencia de `project_id`/`state_id`: `404`, no `422`.**
`docs/contrato-api.md`, "Convenciones", fija "`404` para recurso inexistente"
como regla general, y la sección "Proyectos" ya la aplica a un id de proyecto
inexistente. Una tarea que referencia un `project_id` o `state_id`
inexistente referencia un **recurso** que no existe, no tiene una **forma**
de dato inválida (eso es lo que `422` cubre: título vacío, fecha sin zona). Se
valida primero `project_id` y luego `state_id`; el primero que no exista
determina el `404` devuelto. Aplica igual en `POST` y en `PATCH` (ver
siguiente decisión).

**`PATCH /tasks/{id}` revalida lo que llega en el cuerpo, no solo lo
persiste.** El contrato pide una "actualización parcial **consistente**". Si
el cuerpo trae `project_id`, `state_id` o `title`, se les aplica la misma
validación que en la creación (existencia para las referencias, algoritmo de
normalización para el título) antes de guardar. Justificación: la
Convención "una referencia a proyecto o estado inexistente no se crea
implícitamente" pierde sentido si se puede rodear escribiendo primero y
corrigiendo la referencia después por `PATCH`.

**Algoritmo de normalización de `title`, completo, en un validador
compartido.** `app/schemas.py` gana una función `_normalizar_title(value:
str) -> str` que hace `value.strip()` y luego rechaza (`ValueError`, que
FastAPI convierte en `422`) si **todos** los caracteres restantes caen en las
categorías Unicode `Cc`, `Cf`, `Zl`, `Zp` o `Zs` (incluida la cadena vacía).
La usan `TaskCreate.title` y `TaskUpdate.title` (cuando se envía) como
`field_validator`. Se implementa el algoritmo completo — no una versión
ASCII-only — porque el contrato ya lo fija así; lo que se pospone a la sesión
7 es la batería de prueba exhaustiva, no la implementación (ver "Fuera de
alcance").

**Filtro de listado sin validar existencia.** `GET /tasks?project_id=` o
`?state_id=` con un id que no existe no es `404`: es una búsqueda que no
encuentra nada, y devuelve `200` con lista vacía. El contrato solo exige la
validación de existencia al **crear o actualizar** una tarea (donde la
referencia pasa a formar parte del recurso), no al filtrar una colección.

**`due_at`: se valida y normaliza en el esquema, se sirve sin microsegundos
en la serialización, no al guardar.** Un `field_validator` en modo `"after"`
rechaza (`422`) un valor sin `tzinfo` y convierte el que sí la trae a UTC
(`astimezone(timezone.utc)`) antes de que la ruta lo use; así llega ya
normalizado a la base. La base guarda el valor con la precisión que traiga
(no se recorta al guardar). Un `field_serializer` en `TaskOut.due_at` da el
formato de salida exacto del contrato (`strftime("%Y-%m-%dT%H:%M:%SZ")`), sin
microsegundos, sin desplazamiento. Justificación: el contrato dice "se
serializa siempre en UTC..., sin microsegundos" — es una regla de
serialización, no de almacenamiento.

**`overdue=true` compara por `code`, no por `state_id` fijo.** El filtro hace
`join` de `tasks` con `states` y compara `states.code != 'HECHA'`, en vez de
asumir qué `id` numérico tiene el estado `HECHA`. Justificación: el `id` de
`HECHA` lo asigna la base en el momento del `INSERT` del seed
(`alembic/versions/bfc6b3db4937_*.py`); nada en el contrato garantiza que sea
un valor fijo, y comparar por `code` es correcto sin importar el `id` real.
`overdue=true` se combina con `project_id`/`state_id` si vienen presentes (los
tres son criterios de búsqueda independientes que se combinan con `AND`,
igual que `project_id` y `state_id` entre sí en v1).

**El `409` de `DELETE /projects/{id}` se cierra en este plan.** Ahora que
`tasks` existe, `delete_project` comprueba si existe alguna tarea con ese
`project_id` antes de borrar; si existe, `409` sin borrar nada. Esto cumple
lo que `docs/plan-projects.md` dejó escrito como condición para cerrarlo.

## Incrementos

### Incremento 1 — Migración y modelo de `tasks` (v1, sin `due_at`)

- `alembic/versions/<hash>_crea_la_tabla_tasks.py` (generado con
  `uv run alembic revision -m "crea la tabla tasks"`, encadena tras
  `da291a58134e`): crea `tasks` con `id` (entero, PK), `title`
  (`String(255)`, no nulo), `description` (`Text`, nulo), `project_id`
  (entero, `ForeignKey("projects.id")`, no nulo), `state_id` (entero,
  `ForeignKey("states.id")`, no nulo). Sin seed. `downgrade` elimina la tabla.
- `app/models.py`: añade `class Task(Base)` (`__tablename__ = "tasks"`) con
  esas cinco columnas.
- `tests/test_tasks_migration.py` (test que falla primero, por ausencia de la
  tabla): tras `migrated_db`, `information_schema.columns` para `tasks` tiene
  exactamente `id`, `title`, `description`, `project_id`, `state_id`, con
  `title`/`project_id`/`state_id` `NOT NULL` y `description` nulable;
  `information_schema.table_constraints` / `key_column_usage` confirma las
  dos `FOREIGN KEY` hacia `projects.id` y `states.id`; `downgrade` al
  `down_revision` de esta migración deja `to_regclass('public.tasks')` en
  `NULL`, y se restaura con `upgrade head`.

**Comprobación:**

```bash
docker compose up -d
uv run alembic upgrade head
uv run pytest -q
uv run ruff check .
```

### Incremento 2 — `POST /tasks`, `GET /tasks` (con filtros), `GET /tasks/{id}`

- `app/schemas.py`: función `_normalizar_title`; `TaskCreate` (`title` con el
  validador, `description: str | None = None`, `project_id: int`,
  `state_id: int`); `TaskOut` (`id`, `title`, `description`, `project_id`,
  `state_id`; `extra="forbid"`, `from_attributes=True`). Todavía sin
  `due_at`, tal como el contrato describe el esquema de v1.
- `app/main.py`: `POST /tasks` (`201`; valida `project_id` y `state_id` con
  `session.get` — `404` con el primero que no exista; inserta y devuelve
  `TaskOut`); `GET /tasks` (`200`; parámetros de consulta opcionales
  `project_id: int | None` y `state_id: int | None`, filtran con `AND` si
  ambos vienen; `order_by(Task.id)` siempre, con o sin filtros); `GET
  /tasks/{id}` (`200` o `404`).
- `tests/test_tasks_endpoint.py` (test que falla primero, por ausencia de las
  rutas): creación válida → `201` con esquema exacto (sin `due_at`); título
  vacío y título de solo espacios ASCII → `422` (matriz mínima, sin la
  regresión Unicode de sesión 7); `project_id` inexistente → `404`;
  `state_id` inexistente → `404`; listar sin filtro, con `project_id`, con
  `state_id`, con ambos combinados, y con un filtro que no matchea nada
  (`200` con lista vacía); orden ascendente por `id` estable entre dos
  llamadas idénticas; `GET /tasks/{id}` existente e inexistente (`404`).

**Comprobación:**

```bash
uv run pytest -q
uv run ruff check .
```

### Incremento 3 — `DELETE /projects/{id}` devuelve `409` si el proyecto tiene tareas

- `app/main.py`: `delete_project` consulta primero si existe alguna fila en
  `tasks` con ese `project_id` (`session.execute(select(Task.id).where(...).limit(1))`);
  si existe, `409` sin borrar el proyecto ni la(s) tarea(s); si no, sigue
  igual que hasta ahora (`204`).
- `tests/test_projects_endpoint.py`, casos nuevos: crear un proyecto, crear
  una tarea contra él (`POST /tasks`), `DELETE` al proyecto → `409`, el
  proyecto sigue existiendo (`GET /projects/{id}` → `200`); un proyecto sin
  tareas se sigue borrando con `204` (regresión sobre el caso ya cubierto).

**Comprobación:**

```bash
uv run pytest -q
uv run ruff check .
```

### Incremento 4 — `PATCH /tasks/{id}`

- `app/schemas.py`: `TaskUpdate` (`title: str | None` con el mismo validador
  cuando se envía, `description: str | None = None`, `project_id: int |
  None = None`, `state_id: int | None = None`).
- `app/main.py`: `PATCH /tasks/{id}` — `404` si la tarea no existe; si el
  cuerpo trae `project_id` o `state_id`, revalida su existencia (`404` si no
  existe, mismo orden que en la creación); aplica
  `model_dump(exclude_unset=True)` sobre los campos presentes; `200` con la
  tarea actualizada.
- `tests/test_tasks_endpoint.py`, casos nuevos: actualizar solo `title`
  (conserva el resto); `title` vacío → `422`; `project_id` a uno inexistente
  → `404` (la tarea no cambia); `state_id` a uno inexistente → `404`;
  `PATCH` a id inexistente → `404`.

**Comprobación:**

```bash
uv run pytest -q
uv run ruff check .
```

### Incremento 5 — `DELETE /tasks/{id}`

- `app/main.py`: `DELETE /tasks/{id}` — `404` si no existe; si existe, la
  borra y devuelve `204` sin cuerpo. Sin efectos sobre `projects` ni
  `states`.
- `tests/test_tasks_endpoint.py`, casos nuevos: borrar una tarea existente →
  `204`, `GET` posterior al mismo id → `404`; borrar una tarea deja al
  proyecto borrable si esa era su única tarea (`DELETE /projects/{id}`
  posterior → `204`, cierra el ciclo con el Incremento 3); `DELETE
  /tasks/999999` → `404`.

**Comprobación:**

```bash
uv run pytest -q
uv run ruff check .
```

### Incremento 6 — Migración v2 (`due_at`) y esquema de salida con `due_at`

- `alembic/versions/<hash>_agrega_due_at_a_tasks.py` (encadena tras la
  migración del Incremento 1): `upgrade` añade la columna `due_at`
  (`sa.DateTime(timezone=True)`, nula) a `tasks`; `downgrade` la elimina.
- `app/models.py`: `Task.due_at: Mapped[datetime | None]` con
  `mapped_column(DateTime(timezone=True), nullable=True)`.
- `app/schemas.py`: `due_at: datetime | None = None` en `TaskCreate` y
  `TaskUpdate`, con `field_validator("due_at", mode="after")` que rechaza
  (`422`) un valor sin `tzinfo` y normaliza el que sí la trae a UTC; `due_at:
  datetime | None` en `TaskOut`, con `field_serializer("due_at")` que
  formatea `"%Y-%m-%dT%H:%M:%SZ"` (o `None`).
- `app/main.py`: las rutas de `tasks` ya devuelven `TaskOut`, que ahora
  incluye `due_at`; no hace falta tocar la lógica de las rutas, solo el
  esquema y el modelo.
- `tests/test_tasks_migration.py`, caso nuevo: tras `upgrade head`,
  `information_schema.columns` confirma `due_at` nulable en `tasks`;
  `downgrade` al `down_revision` de esta migración la deja ausente sin tocar
  el resto de columnas, y se restaura con `upgrade head`.
- `tests/test_tasks_endpoint.py`, casos nuevos: crear sin `due_at` → sale
  `null` en el cuerpo; crear con `due_at` con zona (p. ej.
  `"2026-03-01T09:00:00-05:00"`) → sale normalizado
  `"2026-03-01T14:00:00Z"`; crear con `due_at` sin zona
  (`"2026-03-01T09:00:00"`) → `422`; `PATCH` que fija `due_at` sobre una
  tarea que no lo tenía, y `PATCH` con `due_at: null` que lo limpia.

**Comprobación:**

```bash
uv run alembic upgrade head
uv run pytest -q
uv run ruff check .
```

### Incremento 7 — `GET /tasks?overdue=true`

- `app/main.py`: `GET /tasks` gana el parámetro `overdue: bool = False`;
  cuando es `true`, además de los filtros de `project_id`/`state_id` ya
  presentes, hace `join` con `State` y agrega `Task.due_at.is_not(None)`,
  `Task.due_at < datetime.now(timezone.utc)` (instante de evaluación
  calculado en la propia petición) y `State.code != "HECHA"`.
- `tests/test_tasks_endpoint.py`, casos nuevos: tarea con `due_at` en el
  pasado y estado distinto de `HECHA` → aparece en `overdue=true`; tarea con
  `due_at` en el futuro → no aparece; tarea con `due_at` en el pasado pero en
  estado `HECHA` → no aparece; tarea sin `due_at` → no aparece nunca en
  `overdue=true` aunque las demás condiciones se ignoren; `overdue=true`
  combinado con `project_id` sigue aplicando ambos filtros con `AND`.

**Comprobación:**

```bash
uv run pytest -q
uv run ruff check .
```
