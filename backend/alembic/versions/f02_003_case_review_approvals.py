"""Auditable, immutable clinical review evidence tied to an exact case version.

Revision ID: f02_003
Revises: f02_002
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "f02_003"
down_revision = "f02_002"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "case_review_approvals",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("case_version_id", UUID(as_uuid=True), sa.ForeignKey("case_versions.id", ondelete="RESTRICT"), nullable=False, unique=True),
        sa.Column("reviewer_user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("reviewer_name", sa.String(200), nullable=False),
        sa.Column("evidence_reference", sa.String(500), nullable=False),
        sa.Column("blueprint_sha256", sa.String(64), nullable=False),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.execute("ALTER TABLE public.case_review_approvals ENABLE ROW LEVEL SECURITY")
    op.execute("REVOKE ALL ON TABLE public.case_review_approvals FROM anon, authenticated")


def downgrade():
    # Deliberately do not automatically delete irrevocable clinical review audit records.
    raise RuntimeError("Clinical approval audit data must be archived and reviewed before manual rollback")
