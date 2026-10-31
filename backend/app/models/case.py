"""YA-DOK Feature 02: case catalogue, immutable published snapshots, asset references.

This module defines storage only. Student-facing endpoints must not return `blueprint`.
"""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ClinicalCase(Base):
    __tablename__ = "cases"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    # Stable public identifier matching Blueprint.case_id, e.g. PED-RT-0002.
    case_code: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    # NULL => no currently published version. Do not expose draft data to students.
    published_version_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "published_version_number IS NULL OR published_version_number >= 1",
            name="ck_cases_published_version_positive",
        ),
        # A published pointer may only refer to a version belonging to THIS case.
        ForeignKeyConstraint(
            ["id", "published_version_number"],
            ["case_versions.case_id", "case_versions.version_number"],
            name="fk_cases_published_version",
            use_alter=True,
            ondelete="RESTRICT",
        ),
    )


class CaseVersion(Base):
    __tablename__ = "case_versions"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    case_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("cases.id", ondelete="RESTRICT"), nullable=False
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    # Contains medical facts AND secret ground_truth; never return it in a student endpoint.
    blueprint: Mapped[dict] = mapped_column(JSONB, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("case_id", "version_number", name="uq_case_versions_case_number"),
        CheckConstraint("version_number >= 1", name="ck_case_versions_positive"),
    )


class CaseAsset(Base):
    __tablename__ = "case_assets"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    case_version_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("case_versions.id", ondelete="RESTRICT"),
        nullable=False,
    )
    asset_type: Mapped[str] = mapped_column(String(40), nullable=False)
    # Private Supabase Storage object path, never a permanent public URL.
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("case_version_id", "storage_path", name="uq_case_asset_path"),
    )
