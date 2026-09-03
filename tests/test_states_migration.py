"""Tests de la migración del catálogo de estados (incremento 3).

Corren contra PostgreSQL (compose.yaml). Primer test del repo que necesita base.
Acceso async con el engine de la app, coherente con la decisión de ingeniería.
"""

import asyncio

import sqlalchemy as sa
from alembic.script import ScriptDirectory
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import command
from app.db import DATABASE_URL
from tests.conftest import alembic_config

# Códigos del contrato (docs/contrato-api.md, sección Estados).
CONTRACT_CODES = ["PENDIENTE", "EN_CURSO", "BLOQUEADA", "HECHA"]


def _states_revision_module():
    """Carga el módulo de la revisión que crea/siembra `states`."""
    script = ScriptDirectory.from_config(alembic_config())
    for rev in script.walk_revisions():
        if "states" in (rev.doc or "").lower():
            return rev.module
    raise AssertionError("no se encontró la revisión de states")


async def test_upgrade_head_deja_exactamente_los_cuatro_estados(migrated_db):
    engine = create_async_engine(DATABASE_URL)
    try:
        async with engine.connect() as conn:
            result = await conn.execute(
                sa.text("SELECT code FROM states ORDER BY position, id")
            )
            codes = list(result.scalars().all())
    finally:
        await engine.dispose()

    assert codes == CONTRACT_CODES


async def test_reejecutar_el_seed_no_cambia_el_conteo(migrated_db):
    module = _states_revision_module()
    engine = create_async_engine(DATABASE_URL)
    try:
        async with engine.begin() as conn:
            antes = (
                await conn.execute(sa.text("SELECT count(*) FROM states"))
            ).scalar_one()
            # El seed es síncrono (usa la Connection de Alembic); lo corremos
            # sobre la conexión async con run_sync.
            await conn.run_sync(module.seed_states)
            await conn.run_sync(module.seed_states)
            despues = (
                await conn.execute(sa.text("SELECT count(*) FROM states"))
            ).scalar_one()
    finally:
        await engine.dispose()

    assert antes == 4
    assert despues == 4


async def test_downgrade_deja_la_tabla_ausente(migrated_db):
    cfg = alembic_config()
    # Los comandos de Alembic corren su propio event loop (env.py async), así
    # que se ejecutan en un hilo aparte para no chocar con el loop del test.
    await asyncio.to_thread(command.downgrade, cfg, "-1")
    engine = create_async_engine(DATABASE_URL)
    try:
        async with engine.connect() as conn:
            existe = (
                await conn.execute(sa.text("SELECT to_regclass('public.states')"))
            ).scalar()
    finally:
        await engine.dispose()
    # Restaura el estado para el resto de la sesión.
    await asyncio.to_thread(command.upgrade, cfg, "head")

    assert existe is None
