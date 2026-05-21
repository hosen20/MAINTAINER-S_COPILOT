from typing import Any

from sqlalchemy.orm import Session

from app.db.models import AuditLogORM


class AuditRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def write(
        self,
        *,
        action: str,
        target: str,
        actor_user_id: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AuditLogORM:
        row = AuditLogORM(
            actor_user_id=actor_user_id,
            action=action,
            target=target,
            audit_metadata=metadata or {},
        )

        self.session.add(row)
        self.session.flush()
        self.session.refresh(row)

        return row