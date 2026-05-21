from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider

from app.infra.settings import Settings


def configure_tracing(app: FastAPI, settings: Settings) -> None:
    if not settings.tracing_enabled:
        return

    provider = TracerProvider(
        resource=Resource.create({"service.name": settings.tracing_service_name})
    )
    trace.set_tracer_provider(provider)

    FastAPIInstrumentor.instrument_app(app)


def get_tracer(name: str):
    return trace.get_tracer(name)