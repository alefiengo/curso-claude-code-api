"""crea la tabla states y siembra el catálogo

Revision ID: bfc6b3db4937
Revises: b93548d24a12
Create Date: 2026-08-31 20:23:30.170642

El catálogo de estados es cerrado y llega a la base por esta migración, no por
un script de init de Docker (ver docs/contrato-api.md, sección Estados). El seed
es idempotente: `INSERT ... ON CONFLICT (code) DO NOTHING`, de modo que
aplicarlo sobre una base ya poblada no duplica filas.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "bfc6b3db4937"
down_revision: str | Sequence[str] | None = "b93548d24a12"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# Catálogo fijo, en el orden que el contrato declara. `position` es el campo de
# orden que usa `GET /states` (con `id` como desempate).
STATES: tuple[tuple[str, int], ...] = (
    ("PENDIENTE", 1),
    ("EN_CURSO", 2),
    ("BLOQUEADA", 3),
    ("HECHA", 4),
)

states_table = sa.table(
    "states",
    sa.column("code", sa.String),
    sa.column("position", sa.Integer),
)


def seed_states(bind: sa.engine.Connection) -> None:
    """Inserta el catálogo. Idempotente: no toca filas ya presentes."""
    stmt = sa.text(
        "INSERT INTO states (code, position) VALUES (:code, :position) "
        "ON CONFLICT (code) DO NOTHING"
    )
    for code, position in STATES:
        bind.execute(stmt, {"code": code, "position": position})


def upgrade() -> None:
    op.create_table(
        "states",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("position", sa.Integer, nullable=False),
        sa.UniqueConstraint("code", name="uq_states_code"),
    )
    seed_states(op.get_bind())


def downgrade() -> None:
    op.drop_table("states")
