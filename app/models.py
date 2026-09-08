"""Modelos declarativos de la app.

`Base.metadata` es el objetivo de las migraciones de Alembic. El esquema real lo
crean las migraciones; estos modelos describen las tablas para consultarlas
desde la app.
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class State(Base):
    """Catálogo cerrado de estados. Lo siembra la migración, no la API."""

    __tablename__ = "states"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False)


class Project(Base):
    """Proyecto. A diferencia de `State`, sus filas las crea la API."""

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class Task(Base):
    """Tarea. `due_at` (v2) es opcional; se guarda ya normalizada a UTC."""

    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id"), nullable=False
    )
    state_id: Mapped[int] = mapped_column(ForeignKey("states.id"), nullable=False)
    due_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    priority: Mapped[int | None] = mapped_column(Integer, nullable=True)
