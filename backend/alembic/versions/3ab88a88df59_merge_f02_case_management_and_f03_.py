"""merge F02 case management and F03 simulation

Revision ID: 3ab88a88df59
Revises: f02_003, f03_0002
Create Date: 2026-10-30 22:41:57.948454

"""
from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = '3ab88a88df59'
down_revision: str | Sequence[str] | None = ('f02_003', 'f03_0002')
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""


def downgrade() -> None:
    """Downgrade schema."""
