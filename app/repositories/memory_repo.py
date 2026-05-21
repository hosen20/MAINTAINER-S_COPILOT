from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import MemoryORM


class MemoryRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_memory(
        self,
        *,
        actor_user_id: int,
        memory_type: str,
        content: str,
        embedding: list[float] | None,
    ) -> MemoryORM:
        row = MemoryORM(
            actor_user_id=actor_user_id,
            memory_type=memory_type,
            content=content,
            embedding=embedding,
        )

        self.session.add(row)
        self.session.flush()
        self.session.refresh(row)

        return row

    def list_recent_for_user(
        self,
        *,
        actor_user_id: int,
        limit: int = 20,
    ) -> list[MemoryORM]:
        statement = (
            select(MemoryORM)
            .where(MemoryORM.actor_user_id == actor_user_id)
            .order_by(MemoryORM.created_at.desc())
            .limit(limit)
        )

        return list(self.session.scalars(statement).all())