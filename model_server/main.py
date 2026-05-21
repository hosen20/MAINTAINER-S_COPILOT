from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, Field

from model_server.classifier import classify_issue
from model_server.ner import extract_entities
from model_server.summarizer import summarize_issue


app = FastAPI(
    title="Maintainer's Copilot Model Server",
    version="0.1.0",
)


class IssueTextRequest(BaseModel):
    title: str = Field(default="", description="GitHub issue title")
    body: str = Field(default="", description="GitHub issue body")


class ClassificationResponse(BaseModel):
    label: str
    confidence: float
    probabilities: dict[str, float]
    model: str


class Entity(BaseModel):
    type: str
    value: str
    start: int
    end: int


class NERResponse(BaseModel):
    entities: list[Entity]
    count: int
    method: str


class SummaryResponse(BaseModel):
    summary: str
    model: str
    input_chars: int
    used_chars: int | None = None


class AnalyzeResponse(BaseModel):
    classification: dict[str, Any]
    entities: list[Entity]
    entity_count: int
    summary: str


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "model_server"}


@app.post("/classify", response_model=ClassificationResponse)
def classify_endpoint(payload: IssueTextRequest) -> dict:
    return classify_issue(title=payload.title, body=payload.body)


@app.post("/ner", response_model=NERResponse)
def ner_endpoint(payload: IssueTextRequest) -> dict:
    return extract_entities(title=payload.title, body=payload.body)


@app.post("/summarize", response_model=SummaryResponse)
def summarize_endpoint(payload: IssueTextRequest) -> dict:
    return summarize_issue(title=payload.title, body=payload.body)


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze_endpoint(payload: IssueTextRequest) -> dict:
    classification = classify_issue(title=payload.title, body=payload.body)
    ner_result = extract_entities(title=payload.title, body=payload.body)
    summary_result = summarize_issue(title=payload.title, body=payload.body)

    return {
        "classification": classification,
        "entities": ner_result["entities"],
        "entity_count": ner_result["count"],
        "summary": summary_result["summary"],
    }