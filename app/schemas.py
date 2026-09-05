"""Esquemas Pydantic de salida.

Salida estricta: exactamente los campos que declara el contrato
(`docs/contrato-api.md`, sección Esquemas de Respuesta), ni uno más.
"""

from pydantic import BaseModel, ConfigDict, Field


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
