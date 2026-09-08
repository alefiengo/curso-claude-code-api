"""Esquemas Pydantic de salida.

Salida estricta: exactamente los campos que declara el contrato
(`docs/contrato-api.md`, sección Esquemas de Respuesta), ni uno más.
"""

import unicodedata
from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

# Categorías Unicode "invisibles": si un título no deja ningún carácter fuera
# de estas, se considera sin contenido visible (docs/contrato-api.md,
# "Normalización de texto").
_CATEGORIAS_INVISIBLES = {"Cc", "Cf", "Zl", "Zp", "Zs"}


def _normalizar_title(value: str) -> str:
    """Recorta los extremos y rechaza un título sin ningún carácter visible.

    No basta con `strip()`: hay invisibles (p. ej. U+200B) que lo atraviesan.
    """
    value = value.strip()
    if all(unicodedata.category(ch) in _CATEGORIAS_INVISIBLES for ch in value):
        raise ValueError("el título no tiene ningún carácter visible")
    return value


def _normalizar_due_at(value: datetime | None) -> datetime | None:
    """Exige zona horaria y normaliza a UTC. `None` significa "sin fecha"."""
    if value is None:
        return None
    if value.tzinfo is None:
        raise ValueError("due_at debe incluir zona horaria")
    return value.astimezone(UTC)


def _serializar_due_at(value: datetime | None) -> str | None:
    """Formato exacto del contrato: UTC, con `Z`, sin microsegundos."""
    if value is None:
        return None
    return value.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


class StateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: int
    code: str


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1)
    description: str | None = None


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    description: str | None = None


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: int
    name: str
    description: str | None


class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    project_id: int
    state_id: int
    due_at: datetime | None = None

    @field_validator("title")
    @classmethod
    def _validar_title(cls, value: str) -> str:
        return _normalizar_title(value)

    @field_validator("due_at")
    @classmethod
    def _validar_due_at(cls, value: datetime | None) -> datetime | None:
        return _normalizar_due_at(value)


class TaskUpdate(BaseModel):
    # `title`, `project_id` y `state_id` son obligatorios en `Task` (a
    # diferencia de `description`): si se envían, no pueden ser `null`.
    title: str | None = None
    description: str | None = None
    project_id: int | None = None
    state_id: int | None = None
    due_at: datetime | None = None

    @field_validator("title")
    @classmethod
    def _validar_title(cls, value: str | None) -> str:
        if value is None:
            raise ValueError("el título no puede ser nulo")
        return _normalizar_title(value)

    @field_validator("project_id")
    @classmethod
    def _validar_project_id(cls, value: int | None) -> int:
        if value is None:
            raise ValueError("project_id no puede ser nulo")
        return value

    @field_validator("state_id")
    @classmethod
    def _validar_state_id(cls, value: int | None) -> int:
        if value is None:
            raise ValueError("state_id no puede ser nulo")
        return value

    @field_validator("due_at")
    @classmethod
    def _validar_due_at(cls, value: datetime | None) -> datetime | None:
        # A diferencia de title/project_id/state_id, due_at sí puede
        # limpiarse con `null` explícito: es opcional en Task.
        return _normalizar_due_at(value)


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: int
    title: str
    description: str | None
    project_id: int
    state_id: int
    due_at: datetime | None

    @field_serializer("due_at")
    def _serializar_due_at_campo(self, value: datetime | None) -> str | None:
        return _serializar_due_at(value)
