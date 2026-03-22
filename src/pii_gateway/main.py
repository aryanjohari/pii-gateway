"""FastAPI application entrypoint."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from pii_gateway.api.middleware import CorrelationIdMiddleware
from pii_gateway.api.routes_internal import router as internal_router
from pii_gateway.api.routes_sanitize import router as sanitize_router
from pii_gateway.config_loader import load_gateway_policy
from pii_gateway.jobs.scheduler import setup_scheduler, shutdown_scheduler
from pii_gateway.logging_config import setup_logging
from pii_gateway.settings import Settings, load_settings
from pii_gateway.storage.outbound_interface import create_outbound_storage, ensure_state_dir


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    from presidio_analyzer import AnalyzerEngine
    from presidio_anonymizer import AnonymizerEngine

    setup_logging()
    settings = load_settings()
    ensure_state_dir(settings.gateway_state_dir)
    ensure_state_dir(settings.storage_local_path)
    policy = load_gateway_policy(settings)
    analyzer = AnalyzerEngine()
    anonymizer = AnonymizerEngine()  # type: ignore[no-untyped-call]
    app.state.settings = settings
    app.state.policy = policy
    app.state.analyzer = analyzer
    app.state.anonymizer = anonymizer
    app.state.storage = create_outbound_storage(settings)

    engine: AsyncEngine | None = None
    if settings.postgres_batch_dsn and not settings.batch_demo_fixture:
        engine = create_async_engine(settings.postgres_batch_dsn)
    app.state.postgres_engine = engine

    scheduler = None
    if not settings.disable_scheduler:
        scheduler = setup_scheduler(app)
    app.state.scheduler = scheduler

    yield

    if scheduler is not None:
        shutdown_scheduler(scheduler)
    if engine is not None:
        await engine.dispose()


def _register_routes(application: FastAPI) -> None:
    application.include_router(sanitize_router)
    application.include_router(internal_router)

    @application.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @application.exception_handler(RequestValidationError)
    async def _validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        _ = exc
        return JSONResponse(
            status_code=422,
            content={
                "ok": False,
                "error": {"code": "validation_error", "message": "Invalid request body"},
            },
        )

    @application.exception_handler(HTTPException)
    async def _http_handler(request: Request, exc: HTTPException) -> JSONResponse:
        _ = request
        if isinstance(exc.detail, dict) and "code" in exc.detail and "message" in exc.detail:
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "ok": False,
                    "error": {
                        "code": str(exc.detail["code"]),
                        "message": str(exc.detail["message"]),
                    },
                },
            )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "ok": False,
                "error": {"code": "http_error", "message": "Request failed"},
            },
        )


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build application; optional ``settings`` used only for CORS middleware wiring."""
    application = FastAPI(title="PII Gateway", version="0.1.0", lifespan=lifespan)
    application.add_middleware(CorrelationIdMiddleware)
    _register_routes(application)

    cfg = settings or load_settings()
    if cfg.cors_allowed_origins.strip():
        origins = [o.strip() for o in cfg.cors_allowed_origins.split(",") if o.strip()]
        application.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    return application


app = create_app()
