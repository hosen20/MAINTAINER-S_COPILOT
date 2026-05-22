from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class WidgetConfigCreate(BaseModel):
    allowed_origins: list[str] = Field(default_factory=list)
    theme: dict[str, Any] = Field(
        default_factory=lambda: {
            "primary_color": "#2563eb",
            "position": "bottom-right",
        }
    )
    greeting: str = "Hi 👋 How can I help?"
    enabled_tools: list[str] = Field(
        default_factory=lambda: [
            "classifier",
            "ner",
            "summarizer",
            "rag",
            "write_memory",
        ]
    )


class WidgetConfigUpdate(BaseModel):
    allowed_origins: list[str] | None = None
    theme: dict[str, Any] | None = None
    greeting: str | None = None
    enabled_tools: list[str] | None = None
    is_active: bool | None = None


class WidgetConfigRead(BaseModel):
    id: int
    widget_id: str
    allowed_origins: list[str]
    theme: dict[str, Any]
    greeting: str
    enabled_tools: list[str]
    is_active: bool
    created_by_user_id: int | None
    created_at: datetime

    model_config = {
        "from_attributes": True,
    }


class PublicWidgetConfig(BaseModel):
    widget_id: str
    theme: dict[str, Any]
    greeting: str
    enabled_tools: list[str]