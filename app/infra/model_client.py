from __future__ import annotations

from typing import Any

import httpx

from app.domain.errors import ToolFailureError
from app.infra.settings import get_settings


class ModelServerClient:
    def __init__(self, base_url: str | None = None, timeout_seconds: float = 30.0) -> None:
        settings = get_settings()

        if base_url is None:
            base_url = f"http://localhost:{settings.model_server_port}"

        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.base_url}{path}"

        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
                return response.json()

        except httpx.HTTPStatusError as exc:
            raise ToolFailureError(
                f"Model server returned HTTP {exc.response.status_code} for {path}"
            ) from exc

        except httpx.RequestError as exc:
            raise ToolFailureError(
                f"Could not reach model server at {url}"
            ) from exc

    def classify(self, title: str, body: str) -> dict[str, Any]:
        return self._post(
            "/classify",
            {
                "title": title,
                "body": body,
            },
        )

    def extract_entities(self, title: str, body: str) -> dict[str, Any]:
        return self._post(
            "/ner",
            {
                "title": title,
                "body": body,
            },
        )

    def summarize(self, title: str, body: str) -> dict[str, Any]:
        return self._post(
            "/summarize",
            {
                "title": title,
                "body": body,
            },
        )

    def analyze(self, title: str, body: str) -> dict[str, Any]:
        return self._post(
            "/analyze",
            {
                "title": title,
                "body": body,
            },
        )


def get_model_client() -> ModelServerClient:
    return ModelServerClient()