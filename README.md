# TaskFlow API

Base de la API de TaskFlow: FastAPI administrada con [uv](https://docs.astral.sh/uv/)
y Python 3.12.

En esta entrega solo existe `GET /health`. El resto del
[contrato](docs/contrato-api.md) se implementa en sesiones posteriores.

## Requisitos

- Python 3.12 (serie 3.12.x).
- uv.
- Docker con el plugin Compose.

## Recorrido

Todos los comandos se ejecutan desde la raíz del repositorio.

### 1. Instalar dependencias

```bash
uv sync --frozen
```

### 2. Ejecutar los tests

```bash
uv run pytest -q
```

### 3. Pasar el linter

```bash
uv run ruff check .
```

### 4. Levantar PostgreSQL

```bash
docker compose up -d
```

El servicio `db` (PostgreSQL 18-alpine) queda disponible cuando su healthcheck
pasa a `healthy`. `compose.yaml` trae valores por defecto locales, así que
funciona sin `.env`. Para personalizarlo, copia `.env.example` a `.env`.

### 5. Arrancar la API

```bash
uv run uvicorn app.main:app --reload
```

Comprobar la salud:

```bash
curl http://127.0.0.1:8000/health
# {"status":"ok"}
```

### 6. Detener PostgreSQL

```bash
docker compose down
```
