from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import async_session
from app.models import Project, State, Task
from app.schemas import (
    ProjectCreate,
    ProjectOut,
    ProjectUpdate,
    StateOut,
    TaskCreate,
    TaskOut,
    TaskUpdate,
)

app = FastAPI(title="TaskFlow API")


async def get_session() -> AsyncIterator[AsyncSession]:
    async with async_session() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/states", response_model=list[StateOut])
async def list_states(session: SessionDep) -> list[State]:
    # Orden por el campo de catálogo, con id como desempate
    # (docs/contrato-api.md, "Orden de las listas").
    result = await session.execute(select(State).order_by(State.position, State.id))
    return list(result.scalars().all())


@app.post("/projects", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
async def create_project(payload: ProjectCreate, session: SessionDep) -> Project:
    project = Project(name=payload.name, description=payload.description)
    session.add(project)
    await session.commit()
    await session.refresh(project)
    return project


@app.get("/projects", response_model=list[ProjectOut])
async def list_projects(session: SessionDep) -> list[Project]:
    result = await session.execute(select(Project).order_by(Project.id))
    return list(result.scalars().all())


@app.get("/projects/{project_id}", response_model=ProjectOut)
async def get_project(project_id: int, session: SessionDep) -> Project:
    project = await session.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="proyecto no encontrado")
    return project


@app.patch("/projects/{project_id}", response_model=ProjectOut)
async def update_project(
    project_id: int, payload: ProjectUpdate, session: SessionDep
) -> Project:
    project = await session.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="proyecto no encontrado")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(project, field, value)
    await session.commit()
    await session.refresh(project)
    return project


@app.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: int, session: SessionDep) -> None:
    project = await session.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="proyecto no encontrado")
    tiene_tareas = await session.scalar(
        select(Task.id).where(Task.project_id == project_id).limit(1)
    )
    if tiene_tareas is not None:
        raise HTTPException(
            status_code=409, detail="el proyecto tiene tareas asociadas"
        )
    await session.delete(project)
    await session.commit()


@app.post("/tasks", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
async def create_task(payload: TaskCreate, session: SessionDep) -> Task:
    if await session.get(Project, payload.project_id) is None:
        raise HTTPException(status_code=404, detail="proyecto no encontrado")
    if await session.get(State, payload.state_id) is None:
        raise HTTPException(status_code=404, detail="estado no encontrado")
    task = Task(
        title=payload.title,
        description=payload.description,
        project_id=payload.project_id,
        state_id=payload.state_id,
        due_at=payload.due_at,
        priority=payload.priority,
    )
    session.add(task)
    await session.commit()
    await session.refresh(task)
    return task


@app.get("/tasks", response_model=list[TaskOut])
async def list_tasks(
    session: SessionDep,
    project_id: int | None = None,
    state_id: int | None = None,
    overdue: bool = False,
) -> list[Task]:
    query = select(Task).order_by(Task.id)
    if project_id is not None:
        query = query.where(Task.project_id == project_id)
    if state_id is not None:
        query = query.where(Task.state_id == state_id)
    if overdue:
        # Vencida: due_at pasado y estado distinto de HECHA. Se compara por
        # code, no por un state_id fijo (docs/plan-tareas.md, "Decisiones
        # tomadas"). Una tarea sin due_at nunca está vencida.
        query = (
            query.join(State, Task.state_id == State.id)
            .where(Task.due_at.is_not(None))
            .where(Task.due_at < datetime.now(UTC))
            .where(State.code != "HECHA")
        )
    result = await session.execute(query)
    return list(result.scalars().all())


@app.get("/tasks/{task_id}", response_model=TaskOut)
async def get_task(task_id: int, session: SessionDep) -> Task:
    task = await session.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="tarea no encontrada")
    return task


@app.patch("/tasks/{task_id}", response_model=TaskOut)
async def update_task(task_id: int, payload: TaskUpdate, session: SessionDep) -> Task:
    task = await session.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="tarea no encontrada")
    changes = payload.model_dump(exclude_unset=True)
    if "project_id" in changes:
        if await session.get(Project, changes["project_id"]) is None:
            raise HTTPException(status_code=404, detail="proyecto no encontrado")
    if "state_id" in changes:
        if await session.get(State, changes["state_id"]) is None:
            raise HTTPException(status_code=404, detail="estado no encontrado")
    for field, value in changes.items():
        setattr(task, field, value)
    await session.commit()
    await session.refresh(task)
    return task


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int, session: SessionDep) -> None:
    task = await session.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="tarea no encontrada")
    await session.delete(task)
    await session.commit()
