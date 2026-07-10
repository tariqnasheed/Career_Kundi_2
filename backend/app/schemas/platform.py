"""Platform API schemas and response envelopes (0050-PF8-S1)."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ApiListMeta(BaseModel):
    count: int


class SubjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class SubjectEnvelope(BaseModel):
    data: SubjectRead


class SubjectListEnvelope(BaseModel):
    data: list[SubjectRead]
    meta: ApiListMeta


class GoalCreate(BaseModel):
    goal_kind: str
    title: str
    description: str | None = None
    status: str = Field(default="active")


class GoalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    subject_id: uuid.UUID
    goal_kind: str
    title: str
    description: str | None
    status: str
    created_at: datetime
    updated_at: datetime


class GoalEnvelope(BaseModel):
    data: GoalRead


class GoalListEnvelope(BaseModel):
    data: list[GoalRead]
    meta: ApiListMeta
