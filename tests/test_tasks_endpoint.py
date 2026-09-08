"""Tests de los endpoints de Tareas (v1 y v2: `due_at`, `overdue`).

Corren contra PostgreSQL (compose.yaml), app en memoria vía httpx.ASGITransport.
Cada test corre en su propia transacción revertida (ver tests/conftest.py).
"""

import httpx

CODIGOS_TAREA = {
    "id",
    "title",
    "description",
    "project_id",
    "state_id",
    "due_at",
}


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
    assert set(body.keys()) == CODIGOS_TAREA
    assert body["title"] == "Regar las plantas"
    assert body["description"] is None
    assert body["project_id"] == project_id
    assert body["state_id"] == state_id
    assert body["due_at"] is None


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


async def test_patch_task_solo_title_conserva_el_resto(
    client: httpx.AsyncClient,
) -> None:
    project_id = await _crear_project(client)
    state_id = await _primer_state_id(client)
    creada = (
        await client.post(
            "/tasks",
            json={
                "title": "Original",
                "description": "algo",
                "project_id": project_id,
                "state_id": state_id,
            },
        )
    ).json()

    response = await client.patch(
        f"/tasks/{creada['id']}", json={"title": "Actualizada"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Actualizada"
    assert body["description"] == "algo"
    assert body["project_id"] == project_id
    assert body["state_id"] == state_id


async def test_patch_task_con_title_vacio_devuelve_422(
    client: httpx.AsyncClient,
) -> None:
    project_id = await _crear_project(client)
    state_id = await _primer_state_id(client)
    creada = (
        await client.post(
            "/tasks",
            json={"title": "Original", "project_id": project_id, "state_id": state_id},
        )
    ).json()

    response = await client.patch(f"/tasks/{creada['id']}", json={"title": ""})

    assert response.status_code == 422


async def test_patch_task_con_title_null_devuelve_422(
    client: httpx.AsyncClient,
) -> None:
    project_id = await _crear_project(client)
    state_id = await _primer_state_id(client)
    creada = (
        await client.post(
            "/tasks",
            json={"title": "Original", "project_id": project_id, "state_id": state_id},
        )
    ).json()

    response = await client.patch(f"/tasks/{creada['id']}", json={"title": None})

    assert response.status_code == 422


async def test_patch_task_con_project_id_inexistente_devuelve_404_y_no_cambia(
    client: httpx.AsyncClient,
) -> None:
    project_id = await _crear_project(client)
    state_id = await _primer_state_id(client)
    creada = (
        await client.post(
            "/tasks",
            json={"title": "Original", "project_id": project_id, "state_id": state_id},
        )
    ).json()

    response = await client.patch(
        f"/tasks/{creada['id']}", json={"project_id": 999999}
    )

    assert response.status_code == 404
    sin_cambios = (await client.get(f"/tasks/{creada['id']}")).json()
    assert sin_cambios["project_id"] == project_id


async def test_patch_task_con_state_id_inexistente_devuelve_404_y_no_cambia(
    client: httpx.AsyncClient,
) -> None:
    project_id = await _crear_project(client)
    state_id = await _primer_state_id(client)
    creada = (
        await client.post(
            "/tasks",
            json={"title": "Original", "project_id": project_id, "state_id": state_id},
        )
    ).json()

    response = await client.patch(f"/tasks/{creada['id']}", json={"state_id": 999999})

    assert response.status_code == 404
    sin_cambios = (await client.get(f"/tasks/{creada['id']}")).json()
    assert sin_cambios["state_id"] == state_id


async def test_patch_task_inexistente_devuelve_404(
    client: httpx.AsyncClient,
) -> None:
    response = await client.patch("/tasks/999999", json={"title": "Depa"})

    assert response.status_code == 404


async def test_delete_task_existente_devuelve_204_y_luego_404(
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

    response = await client.delete(f"/tasks/{creada['id']}")

    assert response.status_code == 204
    assert response.content == b""

    posterior = await client.get(f"/tasks/{creada['id']}")
    assert posterior.status_code == 404


async def test_delete_task_deja_el_proyecto_borrable_si_era_su_unica_tarea(
    client: httpx.AsyncClient,
) -> None:
    project_id = await _crear_project(client)
    state_id = await _primer_state_id(client)
    tarea_id = (
        await client.post(
            "/tasks",
            json={"title": "Tarea", "project_id": project_id, "state_id": state_id},
        )
    ).json()["id"]

    bloqueado = await client.delete(f"/projects/{project_id}")
    assert bloqueado.status_code == 409

    await client.delete(f"/tasks/{tarea_id}")

    liberado = await client.delete(f"/projects/{project_id}")
    assert liberado.status_code == 204


async def test_delete_task_inexistente_devuelve_404(
    client: httpx.AsyncClient,
) -> None:
    response = await client.delete("/tasks/999999")

    assert response.status_code == 404


async def test_post_tasks_con_due_at_con_zona_se_normaliza_a_utc(
    client: httpx.AsyncClient,
) -> None:
    project_id = await _crear_project(client)
    state_id = await _primer_state_id(client)

    response = await client.post(
        "/tasks",
        json={
            "title": "Tarea",
            "project_id": project_id,
            "state_id": state_id,
            "due_at": "2026-03-01T09:00:00-05:00",
        },
    )

    assert response.status_code == 201
    assert response.json()["due_at"] == "2026-03-01T14:00:00Z"


async def test_post_tasks_con_due_at_sin_zona_devuelve_422(
    client: httpx.AsyncClient,
) -> None:
    project_id = await _crear_project(client)
    state_id = await _primer_state_id(client)

    response = await client.post(
        "/tasks",
        json={
            "title": "Tarea",
            "project_id": project_id,
            "state_id": state_id,
            "due_at": "2026-03-01T09:00:00",
        },
    )

    assert response.status_code == 422


async def test_patch_task_fija_due_at_sobre_tarea_sin_fecha(
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
    assert creada["due_at"] is None

    response = await client.patch(
        f"/tasks/{creada['id']}", json={"due_at": "2026-03-01T09:00:00Z"}
    )

    assert response.status_code == 200
    assert response.json()["due_at"] == "2026-03-01T09:00:00Z"


async def test_patch_task_con_due_at_null_lo_limpia(
    client: httpx.AsyncClient,
) -> None:
    project_id = await _crear_project(client)
    state_id = await _primer_state_id(client)
    creada = (
        await client.post(
            "/tasks",
            json={
                "title": "Tarea",
                "project_id": project_id,
                "state_id": state_id,
                "due_at": "2026-03-01T09:00:00Z",
            },
        )
    ).json()

    response = await client.patch(f"/tasks/{creada['id']}", json={"due_at": None})

    assert response.status_code == 200
    assert response.json()["due_at"] is None
