from pydantic import BaseModel, Field


class WidgetTheme(BaseModel):
    primary_color: str = "#2563eb"
    position: str = "bottom-right"


class WidgetConfig(BaseModel):
    widget_id: str
    allowed_origins: list[str]
    theme: WidgetTheme = Field(default_factory=WidgetTheme)
    greeting: str = "Hi, I am the Maintainer's Copilot."
    enabled_tools: list[str] = Field(default_factory=list)
    is_active: bool = True