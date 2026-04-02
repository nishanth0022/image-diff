"""
FastAPI application entry-point.

Run with:
    uvicorn app.main:app --reload

Swagger UI  →  http://127.0.0.1:8000/docs
ReDoc       →  http://127.0.0.1:8000/redoc
"""

from __future__ import annotations

import logging
import sys

from fastapi import FastAPI

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
#
# WHY NOT logging.basicConfig() here?
#
# Uvicorn calls logging.config.dictConfig() *before* our module is imported,
# so basicConfig() silently does nothing (root logger already has handlers).
#
# FIX: Attach a StreamHandler directly to the "app" package logger.
# Every sub-module that does logging.getLogger("app.xxx") will propagate
# up to this logger and reliably appear in the terminal.
#
_fmt = logging.Formatter("%(asctime)s [%(levelname)-8s] %(name)s: %(message)s")
_handler = logging.StreamHandler(sys.stderr)
_handler.setFormatter(_fmt)
_handler.setLevel(logging.DEBUG)

_pkg_logger = logging.getLogger("app")
_pkg_logger.setLevel(logging.DEBUG)
# Guard against duplicate handlers on --reload
if not any(isinstance(h, logging.StreamHandler) for h in _pkg_logger.handlers):
    _pkg_logger.addHandler(_handler)

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

# openapi_version="3.0.2" is required so that Swagger UI renders
# List[UploadFile] as an array of file-picker buttons instead of plain
# text-string inputs (a known Swagger UI limitation with OpenAPI 3.1).
app = FastAPI(
    title="Image Comparison API",
    description=(
        "Upload a **base** document and one or more **revised** documents "
        "(PNG / JPEG / PDF) and receive a full structured diff report immediately."
    ),
    version="1.0.0",
    openapi_version="3.0.2",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

from app.routes import router  # noqa: E402  (import after app creation)

app.include_router(router)