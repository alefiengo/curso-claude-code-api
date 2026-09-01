"""Metadata declarativa de la app.

`Base.metadata` es el objetivo de las migraciones de Alembic. El incremento 2
no define ninguna tabla todavía; el esquema llega en incrementos posteriores.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
