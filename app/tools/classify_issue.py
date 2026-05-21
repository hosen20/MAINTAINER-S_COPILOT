from __future__ import annotations

from app.domain.classification import ClassificationResult, IssueText
from app.services.classifier_service import ClassifierService


def classify_issue_tool(
    title: str,
    body: str,
) -> ClassificationResult:
    """
    Classify a GitHub issue into one of:
    bug, docs, feature, question.
    """

    service = ClassifierService()

    issue = IssueText(
        title=title,
        body=body,
    )

    return service.classify_issue(issue)