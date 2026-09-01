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

Requisito: `docker compose up -d` con el servicio `db` sano.
"""

import pytest
from alembic.config import Config

from alembic import command
from app.db import DATABASE_URL

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
