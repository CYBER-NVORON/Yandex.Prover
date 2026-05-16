from __future__ import annotations

import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import analyses, health, reports
from app.config import get_settings
from app.database import init_db
from app.services.document_loader import EmptyDocumentError, UnsupportedFormatError
from app.services.llm.base import InvalidLLMResponseError, LLMProviderError
from app.services.storage_service import StorageError


settings = get_settings()

app = FastAPI(
    title="Доказатель API",
    description="Backend API для анализа убедительности материалов перед аудиторией.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(analyses.router)
app.include_router(reports.router)


@app.on_event("startup")
def startup() -> None:
    last_error: Exception | None = None
    for _ in range(12):
        try:
            init_db()
            return
        except Exception as exc:  # pragma: no cover - exercised in docker startup
            last_error = exc
            time.sleep(1)
    if last_error is not None:
        raise last_error


@app.exception_handler(UnsupportedFormatError)
async def unsupported_format_handler(_request: Request, exc: UnsupportedFormatError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(EmptyDocumentError)
async def empty_document_handler(_request: Request, exc: EmptyDocumentError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(InvalidLLMResponseError)
async def invalid_llm_handler(_request: Request, exc: InvalidLLMResponseError) -> JSONResponse:
    return JSONResponse(status_code=502, content={"detail": str(exc)})


@app.exception_handler(LLMProviderError)
async def llm_provider_handler(_request: Request, exc: LLMProviderError) -> JSONResponse:
    return JSONResponse(status_code=503, content={"detail": str(exc)})


@app.exception_handler(StorageError)
async def storage_handler(_request: Request, exc: StorageError) -> JSONResponse:
    return JSONResponse(status_code=500, content={"detail": str(exc)})
