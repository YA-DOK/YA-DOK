"""Add case catalogue, versioned blueprints, and private asset references.

Revision ID: f02_001
Revises: abbade5daee8

No medical records or seed data are included in this migration.
"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "f02_001"
down_revision: str | Sequence[str] | None = "abbade5daee8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "cases",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("case_code", sa.String(length=120), nullable=False),
        sa.Column("published_version_number", sa.Integer(), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("published_version_number IS NULL OR published_version_number >= 1", name="ck_cases_published_version_positive"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("case_code"),
    )
    op.create_table(
        "case_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("blueprint", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("version_number >= 1", name="ck_case_versions_positive"),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("case_id", "version_number", name="uq_case_versions_case_number"),
    )
    # Defined after case_versions exists to resolve the circular reference cleanly.
    op.create_foreign_key(
        "fk_cases_published_version",
        "cases", "case_versions",
        ["id", "published_version_number"],
        ["case_id", "version_number"],
        ondelete="RESTRICT",
    )
    op.create_table(
        "case_assets",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("case_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("asset_type", sa.String(length=40), nullable=False),
        sa.Column("storage_path", sa.String(length=1024), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["case_version_id"], ["case_versions.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("case_version_id", "storage_path", name="uq_case_asset_path"),
    )
    # Deny direct access by anon/authenticated roles. Privileged backend DB connections
    # may bypass RLS: enforce authorization again at every API/service boundary.
    for table in ("cases", "case_versions", "case_assets"):
        op.execute(f"ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    # Only invoke a downgrade in a throwaway local DB after inspecting dependencies.
    op.drop_table("case_assets")
    op.drop_constraint("fk_cases_published_version", "cases", type_="foreignkey")
    op.drop_table("case_versions")
    op.drop_table("cases")
