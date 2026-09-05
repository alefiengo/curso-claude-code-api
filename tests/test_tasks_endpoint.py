"""Tests de los endpoints de Tareas v1 (sin `due_at`, sin `overdue`).

Corren contra PostgreSQL (compose.yaml), app en memoria vía httpx.ASGITransport.
Cada test corre en su propia transacción revertida (ver tests/conftest.py).
"""

import httpx

CODIGOS_ESTADO_V1 = {"id", "title", "description", "project_id", "state_id"}


async def _crear_project(client: httpx.AsyncClient, name: str = "Casa") -> int:
    return (await client.post("/projects", json={"name": name})).json()["id"]


async def _primer_state_id(client: httpx.AsyncClient) -> int:
    return (await client.get("/states")).json()[0]["id"]


async def test_post_tasks_valida_devuelve_201_con_esquema_exacto(
    client: httpx.AsyncClient,
) -> None:
    project_id = await _crear_project(client)
    state_id = await _primer_state_id(client)

    response = await client.post(
        "/tasks",
        json={
            "title": "Regar las plantas",
            "project_id": project_id,
            "state_id": state_id,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert set(body.keys()) == CODIGOS_ESTADO_V1
    assert body["title"] == "Regar las plantas"
    assert body["description"] is None
    assert body["project_id"] == project_id
    assert body["state_id"] == state_id


async def test_post_tasks_con_title_vacio_devuelve_422(
    client: httpx.AsyncClient,
) -> None:
    project_id = await _crear_project(client)
    state_id = await _primer_state_id(client)

    response = await client.post(
        "/tasks", json={"title": "", "project_id": project_id, "state_id": state_id}
    )

    assert response.status_code == 422


async def test_post_tasks_con_title_de_solo_espacios_ascii_devuelve_422(
    client: httpx.AsyncClient,
) -> None:
    project_id = await _crear_project(client)
    state_id = await _primer_state_id(client)

    response = await client.post(
        "/tasks", json={"title": "   ", "project_id": project_id, "state_id": state_id}
    )

    assert response.status_code == 422


async def test_post_tasks_con_project_id_inexistente_devuelve_404(
    client: httpx.AsyncClient,
) -> None:
    state_id = await _primer_state_id(client)

    response = await client.post(
        "/tasks", json={"title": "Tarea", "project_id": 999999, "state_id": state_id}
    )

    assert response.status_code == 404


async def test_post_tasks_con_state_id_inexistente_devuelve_404(
    client: httpx.AsyncClient,
) -> None:
    project_id = await _crear_project(client)

    response = await client.post(
        "/tasks", json={"title": "Tarea", "project_id": project_id, "state_id": 999999}
    )

    assert response.status_code == 404


async def test_get_tasks_lista_en_orden_ascendente_y_es_estable(
    client: httpx.AsyncClient,
) -> None:
    project_id = await _crear_project(client)
    state_id = await _primer_state_id(client)
    creadas = []
    for title in ("Uno", "Dos", "Tres"):
        r = await client.post(
            "/tasks",
            json={"title": title, "project_id": project_id, "state_id": state_id},
        )
        creadas.append(r.json()["id"])

    primera = (await client.get("/tasks")).json()
    segunda = (await client.get("/tasks")).json()

    ids_creadas = set(creadas)
    ids_primera = [item["id"] for item in primera if item["id"] in ids_creadas]
    ids_segunda = [item["id"] for item in segunda if item["id"] in ids_creadas]

    assert ids_primera == sorted(ids_primera)
    assert ids_primera == ids_segunda == creadas


async def test_get_tasks_filtra_por_project_id_y_state_id_solos_y_combinados(
    client: httpx.AsyncClient,
) -> None:
    project_a = await _crear_project(client, "A")
    project_b = await _crear_project(client, "B")
    estados = (await client.get("/states")).json()
    state_1, state_2 = estados[0]["id"], estados[1]["id"]

    t_a1 = (
        await client.post(
            "/tasks",
            json={"title": "a1", "project_id": project_a, "state_id": state_1},
        )
    ).json()["id"]
    t_a2 = (
        await client.post(
            "/tasks",
            json={"title": "a2", "project_id": project_a, "state_id": state_2},
        )
    ).json()["id"]
    (
        await client.post(
            "/tasks",
            json={"title": "b1", "project_id": project_b, "state_id": state_1},
        )
    ).json()["id"]

    solo_project_a = (await client.get(f"/tasks?project_id={project_a}")).json()
    ids_project_a = {t["id"] for t in solo_project_a}
    assert {t_a1, t_a2} <= ids_project_a

    combinado = (
        await client.get(f"/tasks?project_id={project_a}&state_id={state_1}")
    ).json()
    ids_combinado = {t["id"] for t in combinado}
    assert t_a1 in ids_combinado
    assert t_a2 not in ids_combinado


async def test_get_tasks_con_filtro_sin_coincidencias_devuelve_lista_vacia(
    client: httpx.AsyncClient,
) -> None:
    response = await client.get("/tasks?project_id=999999")

    assert response.status_code == 200
    assert response.json() == []


async def test_get_task_por_id_devuelve_el_mismo_cuerpo_que_el_post(
    client: httpx.AsyncClient,
) -> None:
    project_id = await _crear_project(client)
    state_id = await _primer_state_id(client)
    creada = (
        await client.post(
            "/tasks",
            json={"title": "Tarea", "project_id": project_id, "state_id": state_id},
        )
    ).json()

    response = await client.get(f"/tasks/{creada['id']}")

    assert response.status_code == 200
    assert response.json() == creada


async def test_get_task_inexistente_devuelve_404(client: httpx.AsyncClient) -> None:
    response = await client.get("/tasks/999999")

    assert response.status_code == 404
    assert "detail" in response.json()
