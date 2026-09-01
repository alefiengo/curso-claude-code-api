"""Tests del endpoint GET /states (incremento 4).

Corren contra PostgreSQL (compose.yaml), app en memoria vía httpx.ASGITransport.
"""

import httpx

CONTRACT_CODES = ["PENDIENTE", "EN_CURSO", "BLOQUEADA", "HECHA"]


async def test_get_states_devuelve_lista_con_esquema_y_orden(
    client: httpx.AsyncClient,
) -> None:
    response = await client.get("/states")

    assert response.status_code == 200

    body = response.json()
    assert isinstance(body, list)
    assert [item["code"] for item in body] == CONTRACT_CODES

    # Cada elemento tiene exactamente {"id", "code"}, ni un campo más.
    for item in body:
        assert set(item.keys()) == {"id", "code"}

    # Orden por el campo de catálogo con id de desempate: ids ascendentes aquí.
    ids = [item["id"] for item in body]
    assert ids == sorted(ids)


async def test_get_states_es_estable_entre_llamadas_identicas(
    client: httpx.AsyncClient,
) -> None:
    primera = (await client.get("/states")).json()
    segunda = (await client.get("/states")).json()

    assert primera == segunda
    assert [item["id"] for item in primera] == [item["id"] for item in segunda]
