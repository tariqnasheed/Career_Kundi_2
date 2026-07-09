from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.job_search import SavedJobRead


class SavedJobSearchPageRead(BaseModel):
    items: list[SavedJobRead] = Field(
        default_factory=list,
    )
    page: int = Field(
        ge=1,
    )
    page_size: int = Field(
        ge=1,
        le=100,
    )
    has_next: bool
