"""Pin published simulation sessions to immutable case versions."""

from alembic import op

revision = "f02_f03_0001"
down_revision = "3ab88a88df59"
branch_labels = None
depends_on = None


def upgrade():
    op.create_foreign_key(
        "fk_simulation_sessions_case_version",
        "simulation_sessions",
        "case_versions",
        ["case_version_id"],
        ["id"],
        ondelete="RESTRICT",
    )


def downgrade():
    op.drop_constraint(
        "fk_simulation_sessions_case_version",
        "simulation_sessions",
        type_="foreignkey",
    )
