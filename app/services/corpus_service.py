from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.infra.embeddings import EmbeddingClient, get_embedding_client
from app.infra.settings import get_settings
from app.repositories.document_repo import DocumentRepository
from app.services.chunking_service import ChunkingService


DOC_PATHS = [
    "README.md",
    "ARCH.md",
    "DECISIONS.md",
    "MODEL_CARD.md",
    "RUNBOOK.md",
    "EVALS.md",
    "SECURITY.md",
]


class CorpusService:
    def __init__(
        self,
        session: Session,
        embedding_client: EmbeddingClient | None = None,
        chunker: ChunkingService | None = None,
    ) -> None:
        self.session = session
        self.repo = DocumentRepository(session)
        self.embedding_client = embedding_client or get_embedding_client()
        self.chunker = chunker or ChunkingService()
        self.settings = get_settings()

    def rebuild_corpus(
        self,
        *,
        project_root: Path,
        issues_path: Path = Path("data/splits/test.jsonl"),
        clear_existing: bool = True,
        max_issues: int = 150,
    ) -> tuple[int, int]:
        repo_name = self.settings.github_repo

        if clear_existing:
            self.repo.clear_by_repo(repo_name)

        documents_added = 0
        chunks_added = 0

        doc_items = self._load_project_docs(project_root)
        issue_items = self._load_issue_docs(project_root / issues_path, max_issues=max_issues)

        for item in [*doc_items, *issue_items]:
            chunks = self.chunker.chunk_text(
                source_id=item["source_id"],
                title=item["title"],
                text=item["content"],
            )

            embeddings = self.embedding_client.embed_texts([chunk.content for chunk in chunks])

            for chunk, embedding in zip(chunks, embeddings, strict=True):
                metadata = {
                    **item["metadata"],
                    "chunk_id": chunk.chunk_id,
                    "ordinal": chunk.ordinal,
                    "source_id": item["source_id"],
                    "embedding_model": self.embedding_client.model_name,
                    "chunking": {
                        "strategy": "markdown_or_paragraph_boundary_with_overlap",
                        "max_chars": self.chunker.max_chars,
                        "overlap_chars": self.chunker.overlap_chars,
                    },
                }

                self.repo.add_document(
                    source_type=item["source_type"],
                    repo=repo_name,
                    title=chunk.title,
                    content=chunk.content,
                    doc_metadata=metadata,
                    embedding=embedding,
                )
                chunks_added += 1

            documents_added += 1

        self.repo.commit()
        return documents_added, chunks_added

    def _load_project_docs(self, project_root: Path) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []

        for relative_path in DOC_PATHS:
            path = project_root / relative_path
            if not path.exists():
                continue

            content = path.read_text(encoding="utf-8").strip()
            if not content:
                continue

            items.append(
                {
                    "source_id": f"docs::{relative_path}",
                    "source_type": "docs",
                    "title": relative_path,
                    "content": content,
                    "metadata": {"path": relative_path},
                }
            )

        return items

    def _load_issue_docs(self, issues_path: Path, max_issues: int) -> list[dict[str, Any]]:
        if not issues_path.exists():
            return []

        items: list[dict[str, Any]] = []

        with issues_path.open("r", encoding="utf-8") as file:
            for line in file:
                if len(items) >= max_issues:
                    break

                issue = json.loads(line)
                number = issue.get("number")
                title = issue.get("title") or f"Issue {number}"
                body = issue.get("body") or ""
                labels = issue.get("labels") or []
                answerish_text = self._issue_answerish_text(issue)

                content = (
                    f"# {title}\n\n"
                    f"Repo: {issue.get('repo')}\n"
                    f"Issue number: {number}\n"
                    f"Labels: {', '.join(labels)}\n"
                    f"Mapped label: {issue.get('mapped_label')}\n\n"
                    f"Problem description:\n{body}\n\n"
                    f"Maintainer/resolution signal:\n{answerish_text}"
                ).strip()

                items.append(
                    {
                        "source_id": f"issue::{issue.get('repo')}::{number}",
                        "source_type": "issue",
                        "title": title,
                        "content": content,
                        "metadata": {
                            "issue_number": number,
                            "url": issue.get("url"),
                            "mapped_label": issue.get("mapped_label"),
                            "labels": labels,
                            "created_at": issue.get("created_at"),
                            "closed_at": issue.get("closed_at"),
                        },
                    }
                )

        return items

    def _issue_answerish_text(self, issue: dict[str, Any]) -> str:
        comments = issue.get("comments") or issue.get("timeline") or []

        if isinstance(comments, list) and comments:
            text_parts: list[str] = []
            for comment in comments[-3:]:
                if isinstance(comment, dict):
                    body = comment.get("body") or comment.get("text") or ""
                    if body:
                        text_parts.append(body)
            if text_parts:
                return "\n\n".join(text_parts)

        closed_at = issue.get("closed_at")
        mapped_label = issue.get("mapped_label")
        return (
            f"The issue was closed at {closed_at}. "
            f"The maintainer-applied mapped triage label is {mapped_label}. "
            "No maintainer comment text was available in the local dataset."
        )