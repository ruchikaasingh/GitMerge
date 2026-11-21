"""API schemas for persisted conflict review decisions."""

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class ReviewCreate(BaseModel):
    repository_full_name: str | None = Field(default=None, max_length=255)
    pr_number: int | None = Field(default=None, ge=1)
    file_path: str | None = Field(default=None, max_length=1024)
    predicted_strategy: str = Field(min_length=1, max_length=64)
    selected_strategy: str = Field(min_length=1, max_length=64)
    review_status: Literal["accepted", "edited", "deferred"]

    @model_validator(mode="after")
    def require_repository_for_pr(self):
        if self.pr_number is not None and not self.repository_full_name:
            raise ValueError("repository_full_name is required when pr_number is provided.")
        return self
