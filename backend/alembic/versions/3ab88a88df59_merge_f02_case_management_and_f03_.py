"""merge F02 case management and F03 simulation

Revision ID: 3ab88a88df59
Revises: f02_003, f03_0002
Create Date: 2026-10-30 22:41:57.948454

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3ab88a88df59'
down_revision: Union[str, Sequence[str], None] = ('f02_003', 'f03_0002')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
