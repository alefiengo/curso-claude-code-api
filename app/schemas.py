"""Esquemas Pydantic de salida.

Salida estricta: exactamente los campos que declara el contrato
(`docs/contrato-api.md`, sección Esquemas de Respuesta), ni uno más.
"""

from pydantic import BaseModel, ConfigDict


class StateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: int
    code: str
