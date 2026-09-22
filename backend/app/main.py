"""Hasamex FastAPI application."""

from __future__ import annotations

import os
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api import guide, qa, themes, transcripts
from app.api.state import AppContext, build_context
from app.core.config import ConfigError, load_settings
from app.core.logging import configure_logging
from app.core.secrets import redact_secrets
from app.llm.errors import LLMConfigError, LLMError


def create_app(context: AppContext | None = None) -> FastAPI:
    configure_logging(os.getenv("HASAMEX_LOG_LEVEL", "INFO"))
    try:
        settings = context.settings if context is not None else load_settings()
        if context is None:
            settings.require_groq_key()
    except (ConfigError, LLMConfigError) as exc:
        raise SystemExit(str(exc)) from exc

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.context = context if context is not None else build_context(settings)
        yield

    app = FastAPI(
        title="Hasamex AI Analyzer",
        description="Evidence-first expert-call analysis. Quotes come from the transcript store.",
        lifespan=lifespan,
    )
    if context is not None:
        app.state.context = context
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(transcripts.router, prefix="/api")
    app.include_router(guide.router, prefix="/api")
    app.include_router(themes.router, prefix="/api")
    app.include_router(qa.router, prefix="/api")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {
            "status": "ok",
            "llm_provider": settings.llm_provider,
        }

    @app.exception_handler(LLMError)
    async def llm_error_handler(_request: Request, exc: LLMError) -> JSONResponse:
        request_id = str(uuid.uuid4())
        return JSONResponse(
            status_code=exc.http_status,
            content={
                "error": {
                    "code": exc.code,
                    "message": redact_secrets(exc.user_message),
                    "request_id": request_id,
                }
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "The request was invalid.",
                }
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_handler(_request: Request, exc: Exception) -> JSONResponse:
        if isinstance(exc, StarletteHTTPException):
            return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
        if isinstance(exc, LLMError):
            request_id = str(uuid.uuid4())
            return JSONResponse(
                status_code=exc.http_status,
                content={
                    "error": {
                        "code": exc.code,
                        "message": redact_secrets(exc.user_message),
                        "request_id": request_id,
                    }
                },
            )
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred.",
                }
            },
        )

    return app


app = create_app()
