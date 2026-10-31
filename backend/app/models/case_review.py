"""Immutable audit evidence linking a reviewed blueprint snapshot to a verified reviewer.

Never accept the reviewer UUID from the HTTP request body.
"""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, func, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CaseReviewApproval(Base):
    __tablename__ = "case_review_approvals"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    case_version_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("case_versions.id", ondelete="RESTRICT"), nullable=False, unique=True)
    reviewer_user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    reviewer_name: Mapped[str] = mapped_column(String(200), nullable=False)
    evidence_reference: Mapped[str] = mapped_column(String(500), nullable=False)
    blueprint_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    approved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
