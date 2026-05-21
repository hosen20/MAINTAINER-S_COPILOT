from __future__ import annotations

from app.domain.classification import IssueText, SummaryResult
from app.infra.model_client import ModelServerClient, get_model_client


class SummarizerService:
    def __init__(self, model_client: ModelServerClient | None = None) -> None:
        self.model_client = model_client or get_model_client()

    def summarize_issue(self, issue: IssueText) -> SummaryResult:
        result = self.model_client.summarize(
            title=issue.title,
            body=issue.body,
        )

        return SummaryResult.model_validate(result)


def get_summarizer_service() -> SummarizerService:
    return SummarizerService()