"""Tests de la migración de la tabla `tasks` (Tareas v1, sin `due_at`).

Corren contra PostgreSQL (compose.yaml). Como `projects`, sin seed: solo se
verifica el esquema.
"""

import asyncio

import sqlalchemy as sa
from alembic.script import ScriptDirectory
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import command
from app.db import DATABASE_URL
from tests.conftest import alembic_config


def _tasks_v1_revision_module():
    """Carga el módulo de la revisión que crea `tasks` (v1, sin `due_at`)."""
    script = ScriptDirectory.from_config(alembic_config())
    for rev in script.walk_revisions():
        if "crea la tabla tasks" in (rev.doc or "").lower():
            return rev.module
    raise AssertionError("no se encontró la revisión que crea tasks")


async def test_upgrade_head_crea_tasks_con_las_columnas_esperadas(migrated_db):
    engine = create_async_engine(DATABASE_URL)
    try:
        async with engine.connect() as conn:
            result = await conn.execute(
                sa.text(
                    "SELECT column_name, is_nullable FROM information_schema.columns "
                    "WHERE table_name = 'tasks'"
                )
            )
            columns = {row.column_name: row.is_nullable for row in result}

            result = await conn.execute(
                sa.text(
                    "SELECT kcu.column_name, ccu.table_name AS referenced_table "
                    "FROM information_schema.table_constraints tc "
                    "JOIN information_schema.key_column_usage kcu "
                    "  ON tc.constraint_name = kcu.constraint_name "
                    "JOIN information_schema.constraint_column_usage ccu "
                    "  ON tc.constraint_name = ccu.constraint_name "
                    "WHERE tc.table_name = 'tasks' "
                    "AND tc.constraint_type = 'FOREIGN KEY'"
                )
            )
            foreign_keys = {row.column_name: row.referenced_table for row in result}
    finally:
        await engine.dispose()

    assert set(columns.keys()) == {
        "id",
        "title",
        "description",
        "project_id",
        "state_id",
    }
    assert columns["title"] == "NO"
    assert columns["description"] == "YES"
    assert columns["project_id"] == "NO"
    assert columns["state_id"] == "NO"

    assert foreign_keys == {"project_id": "projects", "state_id": "states"}


async def test_downgrade_deja_la_tabla_tasks_ausente(migrated_db):
    cfg = alembic_config()
    # Revisión exacta, no "-1": la cabeza puede tener revisiones posteriores
    # (p. ej. la de due_at) apiladas encima.
    objetivo = _tasks_v1_revision_module().down_revision
    await asyncio.to_thread(command.downgrade, cfg, objetivo)
    engine = create_async_engine(DATABASE_URL)
    try:
        async with engine.connect() as conn:
            existe = (
                await conn.execute(sa.text("SELECT to_regclass('public.tasks')"))
            ).scalar()
    finally:
        await engine.dispose()
    # Restaura el estado para el resto de la sesión.
    await asyncio.to_thread(command.upgrade, cfg, "head")

    assert existe is None
