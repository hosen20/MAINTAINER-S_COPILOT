from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


ChatRole = Literal["system", "user", "assistant", "tool"]


class ChatMessage(BaseModel):
    role: ChatRole
    content: str
    tool_call_id: str | None = None
    name: str | None = None


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    conversation_id: str | None = None
    repo: str | None = None


class ToolCallRecord(BaseModel):
    name: str
    arguments: dict[str, Any]
    result: dict[str, Any] | str


class ChatResponse(BaseModel):
    conversation_id: str
    answer: str
    used_tools: list[ToolCallRecord] = Field(default_factory=list)


class MemoryWriteRequest(BaseModel):
    content: str = Field(min_length=3)
    memory_type: Literal["episodic", "semantic", "procedural"] = "episodic"


class MemoryRead(BaseModel):
    id: int
    actor_user_id: int
    memory_type: str
    content: str
    created_at: datetime