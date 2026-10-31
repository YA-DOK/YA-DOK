
"""Create persistent simulation session and event tables."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "c3f8a91d2b70"
down_revision = "abbade5daee8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "simulation_sessions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "case_version_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column("case_data", postgresql.JSONB(), nullable=False),
        sa.Column(
            "current_phase",
            sa.String(length=40),
            server_default=sa.text("'introduction'"),
            nullable=False,
        ),
        sa.Column(
            "is_paused",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "is_completed",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column("diagnosis", sa.String(), nullable=True),
        sa.Column("treatment_plan", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.create_index(
        "ix_simulation_sessions_user_id",
        "simulation_sessions",
        ["user_id"],
    )
    op.create_index(
        "ix_simulation_sessions_user_created",
        "simulation_sessions",
        ["user_id", "created_at"],
    )

    op.create_table(
        "simulation_events",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(
                "simulation_sessions.id",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("phase", sa.String(length=40), nullable=False),
        sa.Column(
            "details",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "session_id",
            "sequence_number",
            name="uq_simulation_events_session_sequence",
        ),
    )

    op.create_index(
        "ix_simulation_events_session_created",
        "simulation_events",
        ["session_id", "created_at"],
    )

    op.execute(
        "ALTER TABLE public.simulation_events "
        "ENABLE ROW LEVEL SECURITY"
    )

    op.execute(
        "ALTER TABLE public.simulation_sessions "
        "ENABLE ROW LEVEL SECURITY"
    )

def downgrade() -> None:
    op.drop_index(
        "ix_simulation_events_session_created",
        table_name="simulation_events",
    )
    op.drop_table("simulation_events")

    op.drop_index(
        "ix_simulation_sessions_user_created",
        table_name="simulation_sessions",
    )
    op.drop_index(
        "ix_simulation_sessions_user_id",
        table_name="simulation_sessions",
    )
    op.drop_table("simulation_sessions")