from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.auth_routes import get_current_user
from app.api.deps import get_session
from app.domain.auth import AuthenticatedUser
from app.domain.chat import ChatRequest, ChatResponse, MemoryRead, MemoryWriteRequest
from app.services.chat_service import ChatService
from app.services.memory_service import MemoryService


router = APIRouter()


@router.post(
    "",
    response_model=ChatResponse,
)
def chat(
    payload: ChatRequest,
    current_user: Annotated[
        AuthenticatedUser,
        Depends(get_current_user),
    ],
    session: Annotated[
        Session,
        Depends(get_session),
    ],
) -> ChatResponse:
    return ChatService(session).chat(
        actor=current_user,
        payload=payload,
    )


@router.post(
    "/memory",
    response_model=MemoryRead,
)
def write_memory(
    payload: MemoryWriteRequest,
    current_user: Annotated[
        AuthenticatedUser,
        Depends(get_current_user),
    ],
    session: Annotated[
        Session,
        Depends(get_session),
    ],
) -> MemoryRead:
    return MemoryService(session).write_memory(
        actor=current_user,
        payload=payload,
    )


@router.get(
    "/memory",
    response_model=list[MemoryRead],
)
def list_memory(
    current_user: Annotated[
        AuthenticatedUser,
        Depends(get_current_user),
    ],
    session: Annotated[
        Session,
        Depends(get_session),
    ],
    limit: int = Query(default=20, ge=1, le=100),
) -> list[MemoryRead]:
    return MemoryService(session).list_memories(
        actor=current_user,
        limit=limit,
    )