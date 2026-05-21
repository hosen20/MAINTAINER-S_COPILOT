from __future__ import annotations

import json
from pathlib import Path
from statistics import mean

from app.db.session import SessionLocal
from app.domain.rag import GoldenRAGExample, RAGQuery
from app.services.rag_service import RAGService


GOLDEN_PATH = Path("data/golden/rag_golden.jsonl")
REPORT_PATH = Path("data/reports/rag_eval.json")


def load_golden_examples(path: Path) -> list[GoldenRAGExample]:
    examples: list[GoldenRAGExample] = []

    with path.open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                examples.append(GoldenRAGExample.model_validate_json(line))

    return examples


def reciprocal_rank(retrieved: list[str], expected: set[str]) -> float:
    for index, chunk_id in enumerate(retrieved, start=1):
        if chunk_id in expected:
            return 1.0 / index
    return 0.0


def main() -> None:
    examples = load_golden_examples(GOLDEN_PATH)

    if not examples:
        raise RuntimeError(f"No RAG golden examples found in {GOLDEN_PATH}")

    hit_at_5_values: list[float] = []
    mrr_at_10_values: list[float] = []
    retrieved_counts: list[int] = []
    rows: list[dict[str, object]] = []

    with SessionLocal() as session:
        service = RAGService(session)

        for example in examples:
            result = service.answer(
                RAGQuery(
                    question=example.question,
                    repo=example.repo,
                    source_type=example.source_type,
                    top_k=10,
                    use_reranker=True,
                )
            )

            retrieved_chunk_ids = [chunk.chunk_id for chunk in result.chunks]
            expected = set(example.ground_truth_chunk_ids)

            hit_at_5 = float(any(chunk_id in expected for chunk_id in retrieved_chunk_ids[:5]))
            mrr_at_10 = reciprocal_rank(retrieved_chunk_ids[:10], expected)

            hit_at_5_values.append(hit_at_5)
            mrr_at_10_values.append(mrr_at_10)
            retrieved_counts.append(len(retrieved_chunk_ids))

            rows.append(
                {
                    "id": example.id,
                    "question": example.question,
                    "expected": sorted(expected),
                    "retrieved": retrieved_chunk_ids,
                    "hit_at_5": hit_at_5,
                    "mrr_at_10": mrr_at_10,
                    "answer_preview": result.answer[:300],
                }
            )

    report = {
        "hit_at_5": mean(hit_at_5_values),
        "mrr_at_10": mean(mrr_at_10_values),
        "average_retrieved_chunks": mean(retrieved_counts),
        "num_examples": len(examples),
        "examples": rows,
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()