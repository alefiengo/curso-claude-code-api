"""revisión inicial sin cambios de esquema

Revision ID: b93548d24a12
Revises:
Create Date: 2026-08-31 20:17:17.004029

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "b93548d24a12"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Sin operaciones: esta revisión solo fija el punto de partida."""


def downgrade() -> None:
    """Sin operaciones."""
