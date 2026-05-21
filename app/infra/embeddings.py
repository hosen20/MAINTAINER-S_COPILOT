from __future__ import annotations

from functools import lru_cache

import numpy as np
from sentence_transformers import CrossEncoder, SentenceTransformer


DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"


class EmbeddingClient:
    def __init__(self, model_name: str = DEFAULT_EMBEDDING_MODEL) -> None:
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        vectors = self.model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return [vector.astype(float).tolist() for vector in vectors]

    def embed_query(self, text: str) -> list[float]:
        return self.embed_texts([text])[0]


class RerankerClient:
    def __init__(self, model_name: str = DEFAULT_RERANKER_MODEL) -> None:
        self.model_name = model_name
        self.model = CrossEncoder(model_name)

    def score(self, query: str, passages: list[str]) -> list[float]:
        if not passages:
            return []

        pairs = [(query, passage) for passage in passages]
        scores = self.model.predict(pairs)
        return [float(score) for score in np.asarray(scores).tolist()]


@lru_cache
def get_embedding_client() -> EmbeddingClient:
    return EmbeddingClient()


@lru_cache
def get_reranker_client() -> RerankerClient:
    return RerankerClient()