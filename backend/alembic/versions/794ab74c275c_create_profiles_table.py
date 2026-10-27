
"""create profiles table

Revision ID: 794ab74c275c
Revises:
Create Date: 2026-10-08 02:19:28.331524
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# Revision identifiers
revision: str = "794ab74c275c"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create profiles table
    op.create_table(
        "profiles",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("avatar_url", sa.Text(), nullable=True),
        sa.Column(
            "role",
            sa.String(length=20),
            server_default="student",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["id"],
            ["auth.users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Enable Row Level Security
    op.execute(
        "ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY"
    )


def downgrade() -> None:
    # Remove profiles table
    op.drop_table("profiles")
