from __future__ import annotations

from pathlib import Path

from app.db.session import SessionLocal
from app.services.corpus_service import CorpusService


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]

    with SessionLocal() as session:
        service = CorpusService(session)
        documents_added, chunks_added = service.rebuild_corpus(project_root=project_root)

    print(
        {
            "status": "ok",
            "documents_added": documents_added,
            "chunks_added": chunks_added,
        }
    )


if __name__ == "__main__":
    main()