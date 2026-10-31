"""Add complete simulation state and idempotent requests."""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "f03_0002"
down_revision = "c3f8a91d2b70"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "simulation_sessions",
        sa.Column(
            "state_json",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )

    op.create_table(
        "simulation_action_requests",
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(
                "simulation_sessions.id",
                ondelete="CASCADE",
            ),
            primary_key=True,
        ),
        sa.Column(
            "request_id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
        ),
        sa.Column(
            "fingerprint",
            sa.String(64),
            nullable=False,
        ),
        sa.Column(
            "response_json",
            postgresql.JSONB(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    op.execute(
        "ALTER TABLE simulation_action_requests "
        "ENABLE ROW LEVEL SECURITY"
    )


def downgrade():
    op.drop_table("simulation_action_requests")
    op.drop_column("simulation_sessions", "state_json")
