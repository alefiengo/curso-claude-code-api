"""Configuración compartida de los tests.

Estrategia de base de datos para los tests de persistencia
=========================================================

Los tests de persistencia corren contra la misma instancia de PostgreSQL que
levanta `compose.yaml` (nunca SQLite; ver `CLAUDE.md` y
`docs/decisiones-ingenieria.md`). La conexión se toma de `DATABASE_URL`, con el
mismo fallback derivado de los `POSTGRES_*` que usa `app/db.py`.

El fixture `migrated_db` (scope de sesión) aplica `alembic upgrade head` antes
de los tests y `alembic downgrade base` al terminar: el esquema y el catálogo
sembrado existen durante la sesión de tests y se revierten después.

El fixture `client` da un cliente HTTP contra la app en memoria, con la sesión
de base de datos sustituida por un engine creado y desechado dentro del test:
el engine global de `app.db` guarda conexiones atadas a un event loop, y
pytest-asyncio usa un loop por test.

Requisito: `docker compose up -d` con el servicio `db` sano.
"""

from collections.abc import AsyncIterator

import httpx
import pytest
from alembic.config import Config
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from alembic import command
from app.db import DATABASE_URL
from app.main import app, get_session

ALEMBIC_INI = "alembic.ini"


def alembic_config() -> Config:
    cfg = Config(ALEMBIC_INI)
    cfg.set_main_option("sqlalchemy.url", DATABASE_URL)
    return cfg


@pytest.fixture(scope="session")
def migrated_db():
    """Deja la base en `head` durante la sesión y la revierte a `base` al final."""
    cfg = alembic_config()
    command.upgrade(cfg, "head")
    yield
    command.downgrade(cfg, "base")


@pytest.fixture
async def client(migrated_db) -> AsyncIterator[httpx.AsyncClient]:
    engine = create_async_engine(DATABASE_URL)
    sessionmaker = async_sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )

    async def _get_session() -> AsyncIterator[AsyncSession]:
        async with sessionmaker() as session:
            yield session

    app.dependency_overrides[get_session] = _get_session
    transport = httpx.ASGITransport(app=app)
    try:
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as c:
            yield c
    finally:
        app.dependency_overrides.pop(get_session, None)
        await engine.dispose()
