"""Database models for the PR conflict review workflow."""

from datetime import datetime, timezone

from sqlalchemy import DateTime, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class ConflictReview(Base):
    """A review decision and model suggestion, without storing source code."""

    __tablename__ = "conflict_reviews"
    __table_args__ = (
        Index("ix_conflict_reviews_repo_pr_created", "repository_full_name", "pr_number", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    repository_full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    pr_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    file_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    predicted_strategy: Mapped[str] = mapped_column(String(64), nullable=False)
    selected_strategy: Mapped[str] = mapped_column(String(64), nullable=False)
    review_status: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


def to_review_dict(review: ConflictReview) -> dict:
    return {
        "id": review.id,
        "repository_full_name": review.repository_full_name,
        "pr_number": review.pr_number,
        "file_path": review.file_path,
        "predicted_strategy": review.predicted_strategy,
        "selected_strategy": review.selected_strategy,
        "review_status": review.review_status,
        "created_at": review.created_at.isoformat(),
    }
