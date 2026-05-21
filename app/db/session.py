from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.infra.settings import get_settings
from app.infra.vault import VaultClient


def build_database_url() -> str:
    settings = get_settings()
    secrets = VaultClient(settings).read_app_secrets()

    return (
        f"postgresql+psycopg://{settings.postgres_user}:"
        f"{secrets.database_password}@{settings.postgres_host}:"
        f"{settings.postgres_port}/{settings.postgres_db}"
    )


engine = create_engine(build_database_url(), pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()