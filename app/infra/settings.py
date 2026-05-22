from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "maintainers-copilot"
    app_env: str = "local"

    api_port: int = 8000
    model_server_port: int = 8001
    chatbot_port: int = 8501
    widget_port: int = 5173
    host_port: int = 8080

    public_api_base_url: str = "http://localhost:8000"
    widget_app_url: str = "http://localhost:5173"

    vault_addr: str = "http://localhost:8200"
    vault_token: str = "dev-root-token"
    vault_mount: str = "secret"
    vault_secret_path: str = "maintainers-copilot/local"

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "maintainers_copilot"
    postgres_user: str = "mc_app"

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

    minio_endpoint: str = "localhost:9000"
    minio_bucket: str = "maintainers-copilot"
    minio_secure: bool = False

    tracing_enabled: bool = True
    tracing_service_name: str = "maintainers-copilot-api"
    otel_exporter_otlp_endpoint: str = "http://localhost:4317"

    log_level: str = "INFO"
    chat_state_ttl_seconds: int = 7200

    github_repo: str = "tiangolo/fastapi"
    github_token: str | None = None

    model_server_url: str = "http://localhost:8001"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()