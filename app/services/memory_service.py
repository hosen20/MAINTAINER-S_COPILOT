from typing import Any
from uuid import uuid4

from sqlalchemy.orm import Session

from app.domain.auth import AuthenticatedUser
from app.domain.chat import ChatMessage, MemoryRead, MemoryWriteRequest
from app.infra.embeddings import EmbeddingClient, get_embedding_client
from app.infra.redaction import redact_text, redact_value
from app.infra.redis import RedisStateStore, make_redis_client
from app.infra.settings import get_settings
from app.repositories.audit_repo import AuditRepository
from app.repositories.memory_repo import MemoryRepository


class MemoryService:
    def __init__(
        self,
        session: Session,
        embedding_client: EmbeddingClient | None = None,
    ) -> None:
        self.session = session
        self.settings = get_settings()
        self.redis = RedisStateStore(
            client=make_redis_client(self.settings),
            ttl_seconds=self.settings.chat_state_ttl_seconds,
        )
        self.memories = MemoryRepository(session)
        self.audit = AuditRepository(session)
        self.embedding_client = embedding_client or get_embedding_client()

    def new_conversation_id(self) -> str:
        return uuid4().hex

    def get_short_term_messages(
        self,
        *,
        user_id: int,
        conversation_id: str,
    ) -> list[ChatMessage]:
        state = self.redis.get_json(
            self._conversation_key(user_id, conversation_id)
        )

        if not state:
            return []

        return [
            ChatMessage.model_validate(item)
            for item in state.get("messages", [])
        ]

    def save_short_term_messages(
        self,
        *,
        user_id: int,
        conversation_id: str,
        messages: list[ChatMessage],
    ) -> None:
        safe_messages = [
            message.model_copy(
                update={
                    "content": redact_text(message.content),
                }
            ).model_dump()
            for message in messages[-20:]
        ]

        self.redis.set_json(
            self._conversation_key(user_id, conversation_id),
            {
                "conversation_id": conversation_id,
                "messages": safe_messages,
                "ttl_seconds": self.settings.chat_state_ttl_seconds,
            },
        )

    def write_memory(
        self,
        *,
        actor: AuthenticatedUser,
        payload: MemoryWriteRequest,
    ) -> MemoryRead:
        safe_content = redact_text(payload.content)
        embedding = self.embedding_client.embed_query(safe_content)

        row = self.memories.create_memory(
            actor_user_id=actor.id,
            memory_type=payload.memory_type,
            content=safe_content,
            embedding=embedding,
        )

        self.audit.write(
            actor_user_id=actor.id,
            action="memory.write",
            target=f"memory:{row.id}",
            metadata=redact_value(
                {
                    "memory_type": payload.memory_type,
                    "content_preview": safe_content[:120],
                }
            ),
        )

        self.session.commit()

        return MemoryRead(
            id=row.id,
            actor_user_id=row.actor_user_id,
            memory_type=row.memory_type,
            content=row.content,
            created_at=row.created_at,
        )

    def list_memories(
        self,
        *,
        actor: AuthenticatedUser,
        limit: int = 20,
    ) -> list[MemoryRead]:
        rows = self.memories.list_recent_for_user(
            actor_user_id=actor.id,
            limit=limit,
        )

        return [
            MemoryRead(
                id=row.id,
                actor_user_id=row.actor_user_id,
                memory_type=row.memory_type,
                content=row.content,
                created_at=row.created_at,
            )
            for row in rows
        ]

    def format_recent_memories(
        self,
        *,
        actor: AuthenticatedUser,
        limit: int = 8,
    ) -> str:
        memories = self.list_memories(
            actor=actor,
            limit=limit,
        )

        if not memories:
            return "No long-term memories stored yet."

        lines = []
        for memory in memories:
            lines.append(
                f"- [{memory.memory_type}] {memory.content}"
            )

        return "\n".join(lines)

    def _conversation_key(
        self,
        user_id: int,
        conversation_id: str,
    ) -> str:
        return f"chat:{user_id}:{conversation_id}"