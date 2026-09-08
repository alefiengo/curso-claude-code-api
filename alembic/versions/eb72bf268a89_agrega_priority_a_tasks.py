"""agrega priority a tasks

Revision ID: eb72bf268a89
Revises: 6e4d2e01536c
Create Date: 2026-09-07 20:30:27.593811

`priority` (docs/contrato-api.md, sección "Tareas: Prioridad"): entero
opcional, sin rango fijado por el contrato. Revisión propia para poder
revertirla sin tocar `due_at` ni el resto del esquema de `tasks`.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "eb72bf268a89"
down_revision: str | Sequence[str] | None = "6e4d2e01536c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("tasks", sa.Column("priority", sa.Integer, nullable=True))


def downgrade() -> None:
    op.drop_column("tasks", "priority")
