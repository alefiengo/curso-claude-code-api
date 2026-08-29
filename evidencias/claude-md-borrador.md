# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Qué es este repo

API de TaskFlow para un curso de Claude Code. Se construye por sesiones: hoy solo
existe `GET /health` (`app/main.py`); el resto del contrato se implementa después.

## Comandos

Todos desde la raíz del repositorio.

| Acción | Comando |
|---|---|
| Instalar dependencias | `uv sync --frozen` |
| Ejecutar tests | `uv run pytest -q` |
| Un solo test | `uv run pytest tests/test_health.py::test_health_ok` |
| Linter | `uv run ruff check .` |
| Arrancar la API | `uv run uvicorn app.main:app --reload` |
| Verificar salud | `curl http://127.0.0.1:8000/health` |
| Levantar PostgreSQL | `docker compose up -d` |
| Detener PostgreSQL | `docker compose down` |

- Python 3.12 exacto (`requires-python = ">=3.12,<3.13"`). Gestión con `uv`.
- Detener la API: Ctrl-C sobre uvicorn (no hay comando documentado).
- No hay comando de formateo definido; solo `ruff check` con reglas `E, F, I, UP, B`.
- pytest: `asyncio_mode = "auto"`, así que los tests async no necesitan decorador.
  Los tests corren la app en memoria vía `httpx.ASGITransport`, sin servidor.

## El contrato es la fuente de verdad

`docs/contrato-api.md` fija el comportamiento observable de la API. Antes de
implementar cualquier endpoint, léelo. Puntos que gobiernan el diseño:

- **Códigos HTTP del contrato son vinculantes**: no cambies un código sin cambiar
  antes el documento. `404` recurso inexistente, `409` conflicto, `422` entrada
  inválida.
- **Esquemas de respuesta exactos**: ni un campo de más ni de menos. Opcional
  ausente se devuelve como `null`, no se omite. Colecciones devuelven lista JSON
  en la raíz, sin objeto envolvente.
- **Errores**: forma `{"detail": "<mensaje>"}` con mensaje legible, sin filtrar
  internos.
- **Orden estable**: cada colección tiene un orden determinista entre llamadas
  idénticas (ver tabla en el contrato) para que los tests comparen por posición.
- **Normalización de `title`** (tarea): recortar extremos, luego rechazar con
  `422` si no queda ningún carácter visible. La comprobación es por categoría
  Unicode (`Cc`, `Cf`, `Zl`, `Zp`, `Zs`), no basta `strip()`.
- **`due_at`** (tareas v2): siempre serializado en UTC con sufijo `Z`, sin
  microsegundos, sin `+00:00`. Fecha sin zona horaria se rechaza con `422`.
- La "Matriz Mínima de Tests" del contrato lista los casos que los tests deben
  cubrir; pueden añadir más, no debilitar los existentes.

`docs/onboarding.md` (no trackeado) es un mapa del repo con hechos citados por
archivo y línea, y una lista de decisiones aún sin tomar (herramienta de
migración, driver de BD, cómo lee la app la config de conexión).

## Persistencia

- Motor: PostgreSQL 18-alpine vía `compose.yaml`. Defaults locales, funciona sin
  `.env`.
- El catálogo de estados (`PENDIENTE`, `EN_CURSO`, `BLOQUEADA`, `HECHA`) llega a
  la base **por migración**, no por script de init de Docker, y el seed debe ser
  idempotente. Los estados no tienen endpoints de escritura.
- Aún no hay ORM, driver ni herramienta de migración en `pyproject.toml`. Esas
  decisiones se toman en sesiones posteriores.

## Secretos

- `.env` está en `.gitignore` y nunca se commitea. Solo `.env.example` se trackea.
- Credencial nueva: valor ficticio en `.env.example` + valor local en `.env`.
- El `.env.example` solo define variables para Docker Compose, no para la app.
