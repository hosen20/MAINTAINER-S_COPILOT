from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.domain.rag import RAGAnswer, RAGChunk, RAGQuery
from app.services.rag_service import RAGService


router = APIRouter()


def get_rag_service(session: Session = Depends(get_db_session)) -> RAGService:
    return RAGService(session)


@router.post("/answer", response_model=RAGAnswer)
def rag_answer(
    payload: RAGQuery,
    service: RAGService = Depends(get_rag_service),
) -> RAGAnswer:
    return service.answer(payload)


@router.post("/retrieve", response_model=list[RAGChunk])
def rag_retrieve(
    payload: RAGQuery,
    service: RAGService = Depends(get_rag_service),
) -> list[RAGChunk]:
    return service.retrieve(payload)