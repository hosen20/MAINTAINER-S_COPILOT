from fastapi import FastAPI

from app.api.classifier_routes import router as classifier_router
from app.api.exception_handlers import install_exception_handlers
from app.api.health_routes import router as health_router
from app.api.rag_routes import router as rag_router
from app.infra.boot_checks import run_boot_checks
from app.infra.logging import configure_logging
from app.infra.settings import get_settings
from app.infra.tracing import configure_tracing
from app.api.auth_routes import router as auth_router
from app.api.chat_routes import router as chat_router


def create_app() -> FastAPI:
    settings = get_settings()

    configure_logging(settings)
    app = FastAPI(title=settings.app_name)

    configure_tracing(app, settings)
    install_exception_handlers(app)

    app.include_router(health_router, prefix="/health", tags=["health"])
    app.include_router(classifier_router, prefix="/ml", tags=["ml"])
    app.include_router(rag_router, prefix="/rag", tags=["rag"])
    app.include_router(auth_router, prefix="/auth", tags=["auth"])
    app.include_router(chat_router, prefix="/chat", tags=["chat"])

    @app.on_event("startup")
    def startup() -> None:
        run_boot_checks(settings)

    return app


app = create_app()