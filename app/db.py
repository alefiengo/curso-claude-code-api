"""Configuración de acceso a la base de datos.

Acceso async con SQLAlchemy 2.x y asyncpg, según la decisión registrada en
`docs/plan-persistencia.md`. Este módulo solo construye el engine y el
sessionmaker; no abre ninguna conexión al importarse.
"""

import os

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def _default_url() -> str:
    """URL derivada de los POSTGRES_* de Compose, con los mismos defaults."""
    user = os.environ.get("POSTGRES_USER", "taskflow")
    password = os.environ.get("POSTGRES_PASSWORD", "taskflow_local_pw")
    db = os.environ.get("POSTGRES_DB", "taskflow")
    port = os.environ.get("POSTGRES_PORT", "5432")
    return f"postgresql+asyncpg://{user}:{password}@localhost:{port}/{db}"


DATABASE_URL = os.environ.get("DATABASE_URL") or _default_url()

engine = create_async_engine(DATABASE_URL)

async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
