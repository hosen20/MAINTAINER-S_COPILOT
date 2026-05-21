from __future__ import annotations

from app.domain.classification import ClassificationResult, IssueText
from app.infra.model_client import ModelServerClient, get_model_client


class ClassifierService:
    def __init__(self, model_client: ModelServerClient | None = None) -> None:
        self.model_client = model_client or get_model_client()

    def classify_issue(self, issue: IssueText) -> ClassificationResult:
        result = self.model_client.classify(
            title=issue.title,
            body=issue.body,
        )

        return ClassificationResult.model_validate(result)


def get_classifier_service() -> ClassifierService:
    return ClassifierService()