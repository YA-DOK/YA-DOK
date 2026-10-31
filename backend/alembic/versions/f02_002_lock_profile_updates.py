"""Prevent direct client-side profile role updates."""

from alembic import op

revision = "f02_002"
down_revision = "f02_001"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "REVOKE UPDATE ON TABLE public.profiles FROM anon, authenticated"
    )
    op.execute(
        "REVOKE UPDATE (role) ON TABLE public.profiles FROM anon, authenticated"
    )


def downgrade():
    raise RuntimeError(
        "Restoring broad profile UPDATE permissions requires a manual security review."
    )
