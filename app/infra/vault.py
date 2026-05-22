from dataclasses import dataclass
from typing import Any

import hvac

from app.domain.errors import InfrastructureError
from app.infra.settings import Settings


@dataclass(frozen=True)
class AppSecrets:
    database_password: str
    jwt_secret: str
    minio_access_key: str
    minio_secret_key: str
    llm_api_key: str | None = None
    llm_model: str = "llama-3.1-8b-instant"


class VaultClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = hvac.Client(
            url=settings.vault_addr,
            token=settings.vault_token,
        )

    def is_available(self) -> bool:
        return bool(self.client.is_authenticated())

    def read_secret(self) -> dict[str, Any]:
        if not self.is_available():
            raise InfrastructureError("Vault is unreachable or authentication failed")

        response = self.client.secrets.kv.v2.read_secret_version(
            mount_point=self.settings.vault_mount,
            path=self.settings.vault_secret_path,
        )

        return dict(response["data"]["data"])

    def read_app_secrets(self) -> AppSecrets:
        data = self.read_secret()

        return AppSecrets(
            database_password=data["database_password"],
            jwt_secret=data["jwt_secret"],
            minio_access_key=data["minio_access_key"],
            minio_secret_key=data["minio_secret_key"],
            llm_api_key=data.get("llm_api_key"),
            llm_model=data.get("llm_model", "llama-3.1-8b-instant"),
        )