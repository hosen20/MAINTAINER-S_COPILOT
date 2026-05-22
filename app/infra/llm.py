from __future__ import annotations

from typing import Any

import httpx

from app.domain.errors import InfrastructureError
from app.infra.settings import get_settings
from app.infra.vault import VaultClient


class LLMClient:
    def __init__(
        self,
        *,
        base_url: str = "https://api.groq.com/openai/v1",
        timeout_seconds: float = 30.0,
    ) -> None:
        self.settings = get_settings()
        self.secrets = VaultClient(self.settings).read_app_secrets()
        self.base_url = base_url.rstrip("/")
        self.model = self.secrets.llm_model
        self.timeout_seconds = timeout_seconds

    def chat_completion(
        self,
        *,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] = "auto",
        temperature: float = 0.2,
    ) -> dict[str, Any]:
        if not self.secrets.llm_api_key or self.secrets.llm_api_key == "local-placeholder":
            raise InfrastructureError(
                "Missing real Groq API key in Vault. Update llm_api_key before using chat."
            )

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }

        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = tool_choice

        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.secrets.llm_api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )

                response.raise_for_status()

                return response.json()

        except httpx.HTTPStatusError as exc:
            raise InfrastructureError(
                f"LLM provider returned HTTP {exc.response.status_code}: {exc.response.text[:300]}"
            ) from exc

        except httpx.RequestError as exc:
            raise InfrastructureError(
                f"Could not reach LLM provider: {exc}"
            ) from exc