# Reglas de convenciones de la API

## Esquema de respuesta exacto

- Los endpoints viven en `app/main.py`. Cualquier endpoint nuevo o
  modificado responde con el esquema exacto que fija `docs/contrato-api.md`
  (sección "Esquemas de Respuesta"): ni un campo de más ni de menos.

## Campo nuevo: tres capas

- Cualquier campo nuevo en un recurso existente se añade en sus tres capas:
  1. Migración (`alembic/versions/`), que agrega la columna.
  2. Esquema (`app/models.py` y `app/schemas.py`), que la expone y, si
     aplica, la valida.
  3. Validación en el endpoint (`app/main.py`).
- Precedente a seguir: `priority` en `Task` (Lab 01) — entero opcional
  agregado en esas tres capas, con su propia migración y su fila en la
  matriz mínima de `docs/contrato-api.md`.
