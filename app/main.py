from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import async_session
from app.models import Project, State
from app.schemas import ProjectCreate, ProjectOut, ProjectUpdate, StateOut

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
