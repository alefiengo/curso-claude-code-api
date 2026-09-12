"""Errores HTTP reutilizables para los endpoints de `app/main.py`.

Cada excepción fija su propio `status_code` y `detail` para que los
endpoints no repitan el literal (docs/contrato-api.md, "Errores con forma
estable": `{"detail": "<mensaje>"}`). El `422` de validación de Pydantic
queda fuera: no pasa por este módulo (ver `app/schemas.py`).
"""

from fastapi import HTTPException, status


class ProyectoNoEncontrado(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND, detail="proyecto no encontrado"
        )


class EstadoNoEncontrado(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND, detail="estado no encontrado"
        )


class TareaNoEncontrada(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND, detail="tarea no encontrada"
        )


class ProyectoConTareasAsociadas(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="el proyecto tiene tareas asociadas",
        )
