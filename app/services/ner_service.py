from __future__ import annotations

from app.domain.classification import IssueText, NERResult
from app.infra.model_client import ModelServerClient, get_model_client


class NERService:
    def __init__(self, model_client: ModelServerClient | None = None) -> None:
        self.model_client = model_client or get_model_client()

    def extract_entities(self, issue: IssueText) -> NERResult:
        result = self.model_client.extract_entities(
            title=issue.title,
            body=issue.body,
        )

        return NERResult.model_validate(result)


def get_ner_service() -> NERService:
    return NERService()