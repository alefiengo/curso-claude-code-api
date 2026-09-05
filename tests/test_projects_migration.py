"""Tests de la migración de la tabla `projects` (incremento 1 de Proyectos).

Corren contra PostgreSQL (compose.yaml). A diferencia de `states`, `projects`
no lleva seed: solo se verifica el esquema.
"""

import asyncio

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import command
from app.db import DATABASE_URL
from tests.conftest import alembic_config


async def test_upgrade_head_crea_projects_con_las_columnas_esperadas(migrated_db):
    engine = create_async_engine(DATABASE_URL)
    try:
        async with engine.connect() as conn:
            result = await conn.execute(
                sa.text(
                    "SELECT column_name, is_nullable FROM information_schema.columns "
                    "WHERE table_name = 'projects'"
                )
            )
            columns = {row.column_name: row.is_nullable for row in result}
    finally:
        await engine.dispose()

    assert set(columns.keys()) == {"id", "name", "description"}
    assert columns["name"] == "NO"
    assert columns["description"] == "YES"


async def test_downgrade_deja_la_tabla_projects_ausente(migrated_db):
    cfg = alembic_config()
    # Los comandos de Alembic corren su propio event loop (env.py async), así
    # que se ejecutan en un hilo aparte para no chocar con el loop del test.
    await asyncio.to_thread(command.downgrade, cfg, "-1")
    engine = create_async_engine(DATABASE_URL)
    try:
        async with engine.connect() as conn:
            existe = (
                await conn.execute(
                    sa.text("SELECT to_regclass('public.projects')")
                )
            ).scalar()
    finally:
        await engine.dispose()
    # Restaura el estado para el resto de la sesión.
    await asyncio.to_thread(command.upgrade, cfg, "head")

    assert existe is None
