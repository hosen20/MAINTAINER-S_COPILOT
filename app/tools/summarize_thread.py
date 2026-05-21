from __future__ import annotations

from app.domain.classification import IssueText, SummaryResult
from app.services.summarizer_service import SummarizerService


def summarize_thread_tool(
    title: str,
    body: str,
) -> SummaryResult:
    """
    Summarize a GitHub issue or maintainer thread.
    """

    service = SummarizerService()

    issue = IssueText(
        title=title,
        body=body,
    )

    return service.summarize_issue(issue)