from datetime import datetime
from enum import StrEnum
from pydantic import BaseModel, Field


class IssueLabel(StrEnum):
    bug = "bug"
    feature = "feature"
    docs = "docs"
    question = "question"


class IssueRecord(BaseModel):
    external_id: int
    repo: str
    number: int
    title: str
    body: str | None = None
    state: str
    labels: list[str] = Field(default_factory=list)
    mapped_label: IssueLabel | None = None
    created_at: datetime
    closed_at: datetime | None = None
    url: str