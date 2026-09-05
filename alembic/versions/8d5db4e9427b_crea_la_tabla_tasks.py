"""crea la tabla tasks

Revision ID: 8d5db4e9427b
Revises: da291a58134e
Create Date: 2026-09-04 21:00:13.308509

Tareas v1 (docs/contrato-api.md, sección "Tareas v1"). Sin `due_at`: eso
llega en la migración de v2. Sin seed: como `projects`, sus filas las crea la
API.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8d5db4e9427b"
down_revision: str | Sequence[str] | None = "da291a58134e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column(
            "project_id",
            sa.Integer,
            sa.ForeignKey("projects.id"),
            nullable=False,
        ),
        sa.Column(
            "state_id",
            sa.Integer,
            sa.ForeignKey("states.id"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("tasks")
