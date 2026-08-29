# CLAUDE.md

## Fuentes de verdad

- `docs/contrato-api.md` fija el comportamiento observable de la API. Léelo antes
  de implementar o modificar cualquier endpoint. No cambies un código HTTP, un
  esquema de respuesta ni un orden de colección sin cambiar antes ese documento,
  y solo cuando el ticket lo pida de forma explícita.
- `docs/decisiones-ingenieria.md` fija las decisiones de ingeniería del equipo
  (base de datos, migraciones, pruebas, datos locales). No todas se deducen del
  código; consúltalo ante cualquier duda de proceso.
- `README.md` contiene los comandos canónicos del repositorio.

## Comandos canónicos

| Acción | Comando |
|---|---|
| Instalar dependencias | `uv sync --frozen` |
| Ejecutar tests | `uv run pytest -q` |
| Linter | `uv run ruff check .` |

El resto de comandos (arrancar la API, PostgreSQL, verificar salud) está en
`README.md`; no los repitas aquí.

## Pruebas

- Los tests de persistencia corren contra PostgreSQL, nunca SQLite: SQLite no
  reproduce las mismas restricciones, tipos ni migraciones. Detalle en
  `docs/decisiones-ingenieria.md`.
- Una capacidad nueva empieza con un test que falla por su ausencia.
- No debilites ni elimines un test existente para conseguir verde. Si el
  comportamiento acordado cambió, primero cambia el contrato y después el test,
  en un commit separado.
- Los tests async no llevan decorador (`asyncio_mode = "auto"`) y corren la app
  en memoria vía `httpx.ASGITransport`, sin servidor.

## Persistencia

- El esquema cambia mediante migraciones de Alembic, con `upgrade` y `downgrade`
  probados en ambos sentidos. No se crea con efectos al importar módulos ni con
  scripts de init de Docker.
- El catálogo de estados llega a la base por migración y su seed es idempotente.
- Contexto y motivación en `docs/contrato-api.md` (sección Estados) y
  `docs/decisiones-ingenieria.md`.

## Datos locales

- `.env` puede contener secretos: no lo abras, muestres, edites ni lo añadas a
  Git.
- Para conocer nombres de variables usa `.env.example`, la única fuente
  permitida. Los valores reales se configuran fuera de la conversación.
- Credencial nueva: valor ficticio en `.env.example` y valor local en `.env`.
