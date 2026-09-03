from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, FastAPI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import async_session
from app.models import State
from app.schemas import StateOut

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
