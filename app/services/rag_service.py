from __future__ import annotations

import math
import re
from typing import Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sqlalchemy.orm import Session

from app.domain.errors import NotFoundError
from app.domain.rag import RAGAnswer, RAGChunk, RAGQuery
from app.infra.embeddings import (
    EmbeddingClient,
    RerankerClient,
    get_embedding_client,
    get_reranker_client,
)
from app.infra.redaction import redact_text
from app.infra.tracing import get_tracer
from app.repositories.document_repo import DocumentRepository


class RAGService:
    def __init__(
        self,
        session: Session,
        embedding_client: EmbeddingClient | None = None,
        reranker_client: RerankerClient | None = None,
    ) -> None:
        self.session = session
        self.documents = DocumentRepository(session)
        self.embedding_client = embedding_client or get_embedding_client()
        self.reranker_client = reranker_client or get_reranker_client()
        self.tracer = get_tracer(__name__)

    def answer(self, query: RAGQuery) -> RAGAnswer:
        question = redact_text(query.question)
        rewritten_query = self.rewrite_query(question)

        metadata_filter = {
            "repo": query.repo,
            "source_type": query.source_type,
        }

        with self.tracer.start_as_current_span("rag.retrieve") as span:
            span.set_attribute("rag.top_k", query.top_k)
            span.set_attribute("rag.repo", query.repo or "any")
            span.set_attribute("rag.source_type", query.source_type or "any")

            candidate_documents = self.documents.list_documents(
                repo=query.repo,
                source_type=query.source_type,
                limit=2000,
            )

            if not candidate_documents:
                raise NotFoundError(
                    "No RAG documents found. Run `python scripts/build_rag_corpus.py` first."
                )

            chunks = self._hybrid_retrieve(
                question=rewritten_query,
                documents=candidate_documents,
                top_k=max(query.top_k * 4, 20),
            )

            if query.use_reranker:
                chunks = self._rerank(rewritten_query, chunks)

            final_chunks = chunks[: query.top_k]
            answer = self._compose_answer(question, final_chunks)

            span.set_attribute("rag.returned_chunks", len(final_chunks))
            span.set_attribute("rag.strategy", "hybrid_dense_sparse_cross_encoder")

        return RAGAnswer(
            question=question,
            rewritten_query=rewritten_query,
            answer=answer,
            chunks=final_chunks,
            retrieval_strategy=(
                "query_rewrite + metadata_filter + dense_cosine + sparse_tfidf + "
                "weighted_hybrid + cross_encoder_rerank"
            ),
            metadata_filter={k: v for k, v in metadata_filter.items() if v is not None},
        )

    def retrieve(self, query: RAGQuery) -> list[RAGChunk]:
        return self.answer(query).chunks

    def rewrite_query(self, question: str) -> str:
        normalized = re.sub(r"\s+", " ", question).strip()

        expansions = {
            "install": "installation setup configure",
            "auth": "authentication authorization JWT login",
            "login": "authentication JWT user session",
            "db": "database postgres sqlalchemy alembic",
            "database": "postgres sqlalchemy alembic pgvector",
            "docker": "docker compose container service",
            "rag": "retrieval augmented generation chunks embeddings reranking",
            "classify": "classification label bug feature docs question",
            "classifier": "classification label bug feature docs question",
            "trace": "tracing opentelemetry span logs",
            "secret": "vault secret token password key",
        }

        extra_terms: list[str] = []
        lowered = normalized.lower()
        for term, expansion in expansions.items():
            if term in lowered:
                extra_terms.append(expansion)

        if not extra_terms:
            return normalized

        return f"{normalized} {' '.join(extra_terms)}"

    def _hybrid_retrieve(
        self,
        *,
        question: str,
        documents: list[Any],
        top_k: int,
    ) -> list[RAGChunk]:
        contents = [doc.content for doc in documents]
        query_embedding = np.array(self.embedding_client.embed_query(question), dtype=np.float32)

        dense_scores: list[float] = []
        for doc in documents:
            if doc.embedding is None:
                dense_scores.append(0.0)
                continue

            doc_embedding = np.array(doc.embedding, dtype=np.float32)
            dense_scores.append(self._cosine(query_embedding, doc_embedding))

        sparse_scores = self._sparse_scores(question, contents)

        dense_norm = self._normalize(dense_scores)
        sparse_norm = self._normalize(sparse_scores)

        dense_weight = 0.65
        sparse_weight = 0.35

        ranked: list[RAGChunk] = []

        for doc, dense_score, sparse_score in zip(documents, dense_norm, sparse_norm, strict=True):
            hybrid_score = dense_weight * dense_score + sparse_weight * sparse_score
            metadata = dict(doc.doc_metadata or {})
            ranked.append(
                RAGChunk(
                    document_id=doc.id,
                    chunk_id=str(metadata.get("chunk_id", f"document::{doc.id}")),
                    title=doc.title,
                    content=doc.content,
                    source_type=doc.source_type,
                    repo=doc.repo,
                    score=float(hybrid_score),
                    dense_score=float(dense_score),
                    sparse_score=float(sparse_score),
                    metadata=metadata,
                )
            )

        ranked.sort(key=lambda item: item.score, reverse=True)
        return ranked[:top_k]

    def _rerank(self, question: str, chunks: list[RAGChunk]) -> list[RAGChunk]:
        if not chunks:
            return []

        scores = self.reranker_client.score(question, [chunk.content for chunk in chunks])
        updated: list[RAGChunk] = []

        for chunk, rerank_score in zip(chunks, scores, strict=True):
            blended = 0.30 * chunk.score + 0.70 * self._sigmoid(rerank_score)
            updated.append(
                chunk.model_copy(
                    update={
                        "score": float(blended),
                        "rerank_score": float(rerank_score),
                    }
                )
            )

        updated.sort(key=lambda item: item.score, reverse=True)
        return updated

    def _compose_answer(self, question: str, chunks: list[RAGChunk]) -> str:
        if not chunks:
            return "I could not find relevant project context for that question."

        top = chunks[0]
        supporting_titles = ", ".join(dict.fromkeys(chunk.title for chunk in chunks[:3]))

        return (
            f"Based on the retrieved project context, the best answer is in `{top.title}`. "
            f"The relevant evidence says: {self._shorten(top.content, 700)}\n\n"
            f"Supporting sources: {supporting_titles}."
        )

    def _sparse_scores(self, question: str, contents: list[str]) -> list[float]:
        try:
            vectorizer = TfidfVectorizer(
                lowercase=True,
                stop_words="english",
                ngram_range=(1, 2),
                min_df=1,
            )
            matrix = vectorizer.fit_transform(contents)
            query_vector = vectorizer.transform([question])
            scores = (matrix @ query_vector.T).toarray().ravel()
            return [float(score) for score in scores]
        except ValueError:
            return [0.0 for _ in contents]

    def _normalize(self, values: list[float]) -> list[float]:
        if not values:
            return []

        minimum = min(values)
        maximum = max(values)

        if math.isclose(minimum, maximum):
            return [0.0 for _ in values]

        return [(value - minimum) / (maximum - minimum) for value in values]

    def _cosine(self, left: np.ndarray, right: np.ndarray) -> float:
        denominator = float(np.linalg.norm(left) * np.linalg.norm(right))
        if denominator == 0.0:
            return 0.0
        return float(np.dot(left, right) / denominator)

    def _sigmoid(self, value: float) -> float:
        return 1.0 / (1.0 + math.exp(-value))

    def _shorten(self, text: str, limit: int) -> str:
        clean = re.sub(r"\s+", " ", text).strip()
        if len(clean) <= limit:
            return clean
        return clean[:limit].rsplit(" ", 1)[0] + "..."