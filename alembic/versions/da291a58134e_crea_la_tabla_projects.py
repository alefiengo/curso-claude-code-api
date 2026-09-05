"""crea la tabla projects

Revision ID: da291a58134e
Revises: bfc6b3db4937
Create Date: 2026-09-04 20:02:02.810555

A diferencia de `states`, `projects` no es un catálogo cerrado: sus filas las
crea la API (ver docs/contrato-api.md, sección Proyectos). Esta migración solo
crea el esquema, sin seed.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "da291a58134e"
down_revision: str | Sequence[str] | None = "bfc6b3db4937"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
    )


def downgrade() -> None:
    op.drop_table("projects")
