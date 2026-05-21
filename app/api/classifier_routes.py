from __future__ import annotations

from fastapi import APIRouter, Depends

from app.domain.classification import (
    ClassificationResult,
    EntityResult,
    IssueAnalysisResult,
    IssueText,
    NERResult,
    SummaryResult,
)
from app.infra.model_client import ModelServerClient, get_model_client
from app.services.classifier_service import ClassifierService
from app.services.ner_service import NERService
from app.services.summarizer_service import SummarizerService


router = APIRouter()


def get_classifier_service_dep() -> ClassifierService:
    return ClassifierService()


def get_ner_service_dep() -> NERService:
    return NERService()


def get_summarizer_service_dep() -> SummarizerService:
    return SummarizerService()


@router.post("/classify", response_model=ClassificationResult)
def classify_issue(
    payload: IssueText,
    service: ClassifierService = Depends(get_classifier_service_dep),
) -> ClassificationResult:
    return service.classify_issue(payload)


@router.post("/entities", response_model=NERResult)
def extract_entities(
    payload: IssueText,
    service: NERService = Depends(get_ner_service_dep),
) -> NERResult:
    return service.extract_entities(payload)


@router.post("/summarize", response_model=SummaryResult)
def summarize_issue(
    payload: IssueText,
    service: SummarizerService = Depends(get_summarizer_service_dep),
) -> SummaryResult:
    return service.summarize_issue(payload)


@router.post("/analyze", response_model=IssueAnalysisResult)
def analyze_issue(
    payload: IssueText,
    model_client: ModelServerClient = Depends(get_model_client),
) -> IssueAnalysisResult:
    result = model_client.analyze(
        title=payload.title,
        body=payload.body,
    )

    return IssueAnalysisResult(
        classification=ClassificationResult.model_validate(result["classification"]),
        entities=[EntityResult.model_validate(item) for item in result["entities"]],
        entity_count=result["entity_count"],
        summary=result["summary"],
    )