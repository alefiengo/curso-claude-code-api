"""El esquema OpenAPI que la app genera sola.

`openapi.json` en la raíz se exporta desde `app.openapi()` (ver README,
tabla de desarrollo). Estos tests fijan lo que ese esquema debe decir y no
se deduce solo del framework.
"""

from app.main import app


def test_version_de_la_api_es_explicita():
    # El default de FastAPI es "0.1.0"; la versión la elige el equipo, no
    # se hereda. El contrato ya cubre Tareas v1 y v2 completas más priority.
    assert app.openapi()["info"]["version"] == "1.0.0"


def test_due_at_de_salida_declara_formato_date_time():
    # `due_at` se serializa siempre como fecha-hora ISO
    # (docs/contrato-api.md, "Esquemas de Respuesta"). El esquema de salida
    # debe declararlo igual que el de entrada, no como string genérico.
    schemas = app.openapi()["components"]["schemas"]
    salida = schemas["TaskOut"]["properties"]["due_at"]
    formatos = [
        variante.get("format")
        for variante in salida["anyOf"]
        if variante.get("type") == "string"
    ]
    assert "date-time" in formatos
