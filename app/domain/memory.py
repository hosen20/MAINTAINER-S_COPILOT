from datetime import datetime
from enum import StrEnum
from pydantic import BaseModel


class MemoryType(StrEnum):
    episodic = "episodic"
    semantic = "semantic"
    procedural = "procedural"


class MemoryRecord(BaseModel):
    id: int
    actor_user_id: int
    memory_type: MemoryType
    content: str
    created_at: datetime