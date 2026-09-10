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

