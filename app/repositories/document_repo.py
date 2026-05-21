from __future__ import annotations

from typing import Any

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.db.models import DocumentORM


class DocumentRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def clear_by_repo(self, repo: str) -> int:
        result = self.session.execute(delete(DocumentORM).where(DocumentORM.repo == repo))
        self.session.commit()
        return int(result.rowcount or 0)

    def add_document(
        self,
        *,
        source_type: str,
        repo: str,
        title: str,
        content: str,
        doc_metadata: dict[str, Any],
        embedding: list[float] | None,
    ) -> DocumentORM:
        document = DocumentORM(
            source_type=source_type,
            repo=repo,
            title=title,
            content=content,
            doc_metadata=doc_metadata,
            embedding=embedding,
        )
        self.session.add(document)
        self.session.flush()
        return document

    def commit(self) -> None:
        self.session.commit()

    def list_documents(
        self,
        *,
        repo: str | None = None,
        source_type: str | None = None,
        limit: int = 2000,
    ) -> list[DocumentORM]:
        query = self.session.query(DocumentORM)

        if repo:
            query = query.filter(DocumentORM.repo == repo)

        if source_type:
            query = query.filter(DocumentORM.source_type == source_type)

        return query.order_by(DocumentORM.id.desc()).limit(limit).all()

    def get_by_chunk_ids(self, chunk_ids: list[str]) -> list[DocumentORM]:
        if not chunk_ids:
            return []

        return (
            self.session.query(DocumentORM)
            .filter(DocumentORM.doc_metadata["chunk_id"].astext.in_(chunk_ids))
            .all()
        )