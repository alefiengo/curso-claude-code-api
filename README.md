# TaskFlow API

API de TaskFlow: FastAPI sobre PostgreSQL, administrada con
[uv](https://docs.astral.sh/uv/) y Python 3.12.

El comportamiento observable de la API está fijado en
[`docs/contrato-api.md`](docs/contrato-api.md). Las peticiones de ejemplo, una
por método y ruta, están en [`api.http`](api.http).

## Requisitos

- Python 3.12 (serie 3.12.x).
- uv.
- Docker con el plugin Compose.

## Puesta en marcha

Todos los comandos se ejecutan desde la raíz del repositorio.

1. Instala las dependencias:

   ```bash
   uv sync --frozen
   ```

2. Copia la plantilla de variables de entorno:

   ```bash
   cp .env.example .env
   ```

3. Levanta PostgreSQL y espera a que su healthcheck pase a `healthy`:

   ```bash
   docker compose up -d
   ```

4. Aplica las migraciones (crea el esquema y siembra el catálogo de estados):

   ```bash
   uv run alembic upgrade head
   ```

5. Arranca la API en `http://127.0.0.1:8000`:

   ```bash
   uv run uvicorn app.main:app --reload
   ```

6. Comprueba que responde:

   ```bash
   curl http://127.0.0.1:8000/health
   # {"status":"ok"}
   ```

7. Prueba el resto de endpoints ejecutando los bloques de
   [`api.http`](api.http) de arriba abajo, con la extensión REST Client de VS
   Code o cualquier cliente compatible.

## Parar

- Detén la API con Ctrl-C sobre el proceso de uvicorn.
- Detén PostgreSQL:

  ```bash
  docker compose down
  ```

## Desarrollo

| Acción | Comando |
|---|---|
| Ejecutar los tests | `uv run pytest -q` |
| Pasar el linter | `uv run ruff check .` |
| Revertir todas las migraciones | `uv run alembic downgrade base` |
| Regenerar `openapi.json` | `uv run python -c "import json, sys; from app.main import app; json.dump(app.openapi(), sys.stdout, indent=2, ensure_ascii=False); print()" > openapi.json` |

Los tests de persistencia corren contra la instancia de PostgreSQL de
`docker compose`; tenla levantada antes de `uv run pytest -q`.
