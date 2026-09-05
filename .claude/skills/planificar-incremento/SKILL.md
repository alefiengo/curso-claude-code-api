---
name: planificar-incremento
description: >-
  Planifica un incremento de trabajo de este repositorio contra el contrato y
  las decisiones de ingeniería del equipo. Produce un plan en docs/ dividido en
  incrementos numerados, cada uno con su comprobación ejecutable, sin dejar
  ninguna decisión aplazada. Úsala cuando el usuario pida planificar una sesión,
  un endpoint, una capacidad o un cambio antes de implementarlo. Planifica, no
  implementa.
---

# Planificar un incremento

Esta skill produce un **plan escrito**. No implementa nada.

## Contra qué se planifica

Lee, en este orden, antes de escribir una sola línea del plan:

1. `docs/contrato-api.md` — comportamiento observable de la API: códigos HTTP,
   esquemas de respuesta exactos, orden de las colecciones, normalización de
   texto, matriz mínima de tests. Es la fuente de verdad. No se planifica un
   cambio de contrato salvo que el encargo lo pida de forma explícita.
2. `docs/decisiones-ingenieria.md` — decisiones del equipo que no se deducen del
   código: base de datos, migraciones, estrategia de pruebas, datos locales.
3. `CLAUDE.md` — reglas del repositorio y comandos canónicos.
4. `README.md` — comandos canónicos exactos (instalar, tests, linter, arrancar,
   Postgres).
5. El historial relevante: `git log` y los planes previos en `docs/` (por
   ejemplo `docs/plan-persistencia.md`), para no repetir decisiones ya tomadas
   ni contradecirlas.

Si el encargo menciona un documento adicional (un ticket, una nota de sesión en
`evidencias/`), léelo también.

## Qué produce

Un archivo Markdown en **`docs/`** con un nombre que diga de qué es el plan:
`docs/plan-<tema>.md` (por ejemplo `docs/plan-projects.md`,
`docs/plan-tareas-v2.md`). Si ya existe un archivo con ese nombre, propón otro o
pregunta antes de sobrescribir.

### Estructura del archivo

- **Título y una frase** de qué cubre el plan y qué no.
- **Fuentes** — los documentos concretos contra los que se planificó, con las
  secciones relevantes.
- **Fuera de alcance** — lista explícita de lo que este plan NO aborda. No puede
  quedar implícito: nómbralo.
- **Estado del repositorio al planificar** — qué existe hoy relevante para el
  encargo (endpoints, modelos, migraciones, dependencias), citando archivo.
- **Decisiones tomadas** — cada decisión con su justificación trazada a un
  documento o al código. Ver la regla de abajo.
- **Incrementos** — numerados (Incremento 1, 2, 3…). Cada uno:
  - Un objetivo de una frase.
  - Los archivos que tocaría.
  - **Comprobación** — los comandos exactos que otra persona ejecutaría para
    verificar ese incremento, y el resultado esperado. Usa los comandos
    canónicos del `README.md` / `CLAUDE.md` (`uv run pytest -q`,
    `uv run ruff check .`, `uv run alembic upgrade head` / `downgrade base`,
    `docker compose up -d`, `curl` a un endpoint). Una capacidad nueva empieza
    por un test que falla por su ausencia.

## Regla: ninguna decisión aplazada

No se admite una sección de "decisiones abiertas" ni frases en condicional del
tipo "se podría usar X" o "quizá convenga Y".

- Si la decisión **se puede tomar** con lo que hay en el repositorio (contrato,
  decisiones de ingeniería, código, planes previos), tómala y escribe la
  justificación.
- Si **no se puede tomar** con lo que hay, **pregúntale al usuario** ahí mismo,
  antes de terminar el plan. No la dejes escrita como propuesta tentativa.

## Fuera de alcance de la skill

Esta skill **planifica y no implementa**. Dentro de esta skill:

- No se crea ni se modifica código de la aplicación ni de los tests.
- No se instalan ni se cambian dependencias (`uv sync`, `pyproject.toml`).
- No se toca la base de datos: no se aplican migraciones, no se ejecutan
  `alembic upgrade`/`downgrade`, no se levanta ni consulta PostgreSQL.
- El único archivo que se crea o modifica es el plan en `docs/`.

Los comandos de comprobación van **escritos en el plan** para que otra persona
los ejecute; la skill no los ejecuta.

## No abrir .env

`.env` puede tener secretos. Para nombres de variables usa `.env.example`.
