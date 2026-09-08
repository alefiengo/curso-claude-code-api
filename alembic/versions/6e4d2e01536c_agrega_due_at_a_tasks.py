"""agrega due_at a tasks

Revision ID: 6e4d2e01536c
Revises: 8d5db4e9427b
Create Date: 2026-09-07 19:24:39.530979

Tareas v2 (docs/contrato-api.md, sección "Tareas v2: Fechas Límite").
`due_at` es opcional y se guarda con zona horaria; la app normaliza a UTC
antes de guardar (ver app/schemas.py). Revisión propia, no fusionada con la
de v1, para poder revertir solo v2 (matriz mínima de tests: "rollback de
v2").
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6e4d2e01536c"
down_revision: str | Sequence[str] | None = "8d5db4e9427b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "tasks", sa.Column("due_at", sa.DateTime(timezone=True), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("tasks", "due_at")
