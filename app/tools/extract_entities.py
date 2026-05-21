from __future__ import annotations

from app.domain.classification import IssueText, NERResult
from app.services.ner_service import NERService


def extract_entities_tool(
    title: str,
    body: str,
) -> NERResult:
    """
    Extract code-shaped entities from a GitHub issue:
    file paths, versions, errors, commands, Kubernetes components, issue refs.
    """

    service = NERService()

    issue = IssueText(
        title=title,
        body=body,
    )

    return service.extract_entities(issue)