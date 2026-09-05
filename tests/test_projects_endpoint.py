"""Tests de los endpoints de Proyectos.

Corren contra PostgreSQL (compose.yaml), app en memoria vía httpx.ASGITransport.
Cada test corre en su propia transacción revertida (ver tests/conftest.py), así
que los proyectos que crea no contaminan a otros tests.
"""

import httpx


async def test_post_projects_sin_description_devuelve_201_con_esquema_exacto(
    client: httpx.AsyncClient,
) -> None:
    response = await client.post("/projects", json={"name": "Casa"})

    assert response.status_code == 201
    body = response.json()
    assert set(body.keys()) == {"id", "name", "description"}
    assert body["name"] == "Casa"
    assert body["description"] is None
    assert isinstance(body["id"], int)


async def test_post_projects_con_description_la_conserva(
    client: httpx.AsyncClient,
) -> None:
    response = await client.post(
        "/projects", json={"name": "Casa", "description": "Tareas del hogar"}
    )

    assert response.status_code == 201
    assert response.json()["description"] == "Tareas del hogar"


async def test_post_projects_con_name_vacio_devuelve_422(
    client: httpx.AsyncClient,
) -> None:
    response = await client.post("/projects", json={"name": ""})

    assert response.status_code == 422


async def test_get_projects_lista_en_orden_ascendente_y_es_estable(
    client: httpx.AsyncClient,
) -> None:
    creados = []
    for name in ("Uno", "Dos", "Tres"):
        r = await client.post("/projects", json={"name": name})
        creados.append(r.json()["id"])

    primera = (await client.get("/projects")).json()
    segunda = (await client.get("/projects")).json()

    ids_creados = set(creados)
    ids_primera = [item["id"] for item in primera if item["id"] in ids_creados]
    ids_segunda = [item["id"] for item in segunda if item["id"] in ids_creados]

    assert ids_primera == sorted(ids_primera)
    assert ids_primera == ids_segunda == creados


async def test_get_project_por_id_devuelve_el_mismo_cuerpo_que_el_post(
    client: httpx.AsyncClient,
) -> None:
    creado = (await client.post("/projects", json={"name": "Casa"})).json()

    response = await client.get(f"/projects/{creado['id']}")

    assert response.status_code == 200
    assert response.json() == creado


async def test_get_project_inexistente_devuelve_404(
    client: httpx.AsyncClient,
) -> None:
    response = await client.get("/projects/999999")

    assert response.status_code == 404
    assert "detail" in response.json()


async def test_patch_project_solo_name_conserva_description(
    client: httpx.AsyncClient,
) -> None:
    creado = (
        await client.post(
            "/projects", json={"name": "Casa", "description": "Tareas del hogar"}
        )
    ).json()

    response = await client.patch(f"/projects/{creado['id']}", json={"name": "Depa"})

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Depa"
    assert body["description"] == "Tareas del hogar"


async def test_patch_project_description_null_explicito_la_limpia(
    client: httpx.AsyncClient,
) -> None:
    creado = (
        await client.post(
            "/projects", json={"name": "Casa", "description": "Tareas del hogar"}
        )
    ).json()

    response = await client.patch(
        f"/projects/{creado['id']}", json={"description": None}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Casa"
    assert body["description"] is None


async def test_patch_project_con_name_vacio_devuelve_422(
    client: httpx.AsyncClient,
) -> None:
    creado = (await client.post("/projects", json={"name": "Casa"})).json()

    response = await client.patch(f"/projects/{creado['id']}", json={"name": ""})

    assert response.status_code == 422


async def test_patch_project_inexistente_devuelve_404(
    client: httpx.AsyncClient,
) -> None:
    response = await client.patch("/projects/999999", json={"name": "Depa"})

    assert response.status_code == 404


async def test_delete_project_existente_devuelve_204_y_luego_404(
    client: httpx.AsyncClient,
) -> None:
    creado = (await client.post("/projects", json={"name": "Casa"})).json()

    response = await client.delete(f"/projects/{creado['id']}")

    assert response.status_code == 204
    assert response.content == b""

    posterior = await client.get(f"/projects/{creado['id']}")
    assert posterior.status_code == 404


async def test_delete_project_inexistente_devuelve_404(
    client: httpx.AsyncClient,
) -> None:
    response = await client.delete("/projects/999999")

    assert response.status_code == 404


async def test_delete_project_con_tareas_devuelve_409_y_no_borra(
    client: httpx.AsyncClient,
) -> None:
    project_id = (await client.post("/projects", json={"name": "Casa"})).json()["id"]
    state_id = (await client.get("/states")).json()[0]["id"]
    await client.post(
        "/tasks",
        json={"title": "Tarea", "project_id": project_id, "state_id": state_id},
    )

    response = await client.delete(f"/projects/{project_id}")

    assert response.status_code == 409
    assert "detail" in response.json()

    posterior = await client.get(f"/projects/{project_id}")
    assert posterior.status_code == 200
