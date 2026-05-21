from datetime import datetime
from pydantic import BaseModel


class AuditLogRecord(BaseModel):
    id: int
    actor_user_id: int | None
    action: str
    target: str
    metadata: dict
    created_at: datetime