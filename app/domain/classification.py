from __future__ import annotations

from pydantic import BaseModel, Field


class IssueText(BaseModel):
    title: str = Field(default="", description="GitHub issue title")
    body: str = Field(default="", description="GitHub issue body")


class ClassificationResult(BaseModel):
    label: str
    confidence: float
    probabilities: dict[str, float]
    model: str


class EntityResult(BaseModel):
    type: str
    value: str
    start: int
    end: int


class NERResult(BaseModel):
    entities: list[EntityResult]
    count: int
    method: str


class SummaryResult(BaseModel):
    summary: str
    model: str
    input_chars: int
    used_chars: int | None = None


class IssueAnalysisResult(BaseModel):
    classification: ClassificationResult
    entities: list[EntityResult]
    entity_count: int
    summary: str