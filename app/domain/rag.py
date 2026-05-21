from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class RAGQuery(BaseModel):
    question: str = Field(min_length=3)
    repo: str | None = None
    source_type: str | None = None
    top_k: int = Field(default=5, ge=1, le=20)
    use_reranker: bool = True


class RAGChunk(BaseModel):
    document_id: int
    chunk_id: str
    title: str
    content: str
    source_type: str
    repo: str
    score: float
    dense_score: float | None = None
    sparse_score: float | None = None
    rerank_score: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class RAGAnswer(BaseModel):
    question: str
    rewritten_query: str
    answer: str
    chunks: list[RAGChunk]
    retrieval_strategy: str
    metadata_filter: dict[str, Any] = Field(default_factory=dict)


class CorpusBuildResult(BaseModel):
    documents_added: int
    chunks_added: int
    repo: str


class GoldenRAGExample(BaseModel):
    id: str
    question: str
    ideal_answer: str
    ground_truth_chunk_ids: list[str]
    repo: str | None = None
    source_type: Literal["issue", "docs"] | None = None