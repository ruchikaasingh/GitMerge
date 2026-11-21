"""Create the conflict review history table."""

from alembic import op
import sqlalchemy as sa


revision = "0001_conflict_reviews"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "conflict_reviews",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("repository_full_name", sa.String(length=255), nullable=True),
        sa.Column("pr_number", sa.Integer(), nullable=True),
        sa.Column("file_path", sa.String(length=1024), nullable=True),
        sa.Column("predicted_strategy", sa.String(length=64), nullable=False),
        sa.Column("selected_strategy", sa.String(length=64), nullable=False),
        sa.Column("review_status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_conflict_reviews_repo_pr_created",
        "conflict_reviews",
        ["repository_full_name", "pr_number", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_conflict_reviews_repo_pr_created", table_name="conflict_reviews")
    op.drop_table("conflict_reviews")
