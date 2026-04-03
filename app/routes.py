"""
FastAPI route handlers for the Image Comparison API.

POST /compare/
    Upload a base document + one or more revised documents.
    The pipeline runs synchronously and returns results immediately.

GET /
    Liveness / health check.
"""

from __future__ import annotations

import asyncio
import logging
import os
import shutil
import uuid
from typing import List

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse

from app.comparison.diff_engine import detect_differences
from app.comparison.matcher import match
from app.detection.graphics_detector import detect_graphics
from app.detection.text_detector import detect_text
from app.detection.barcode_detector import detect_barcodes
from app.ingestion.loader import load_file
from app.models.schemas import CompareResponse, ComparisonResult, DiffItem
from app.preprocessing.preprocess import preprocess
from app.reporting.report_generator import generate_html, generate_json

logger = logging.getLogger("app.routes")

router = APIRouter()

UPLOAD_DIR = "uploads"
OUTPUT_DIR = "output"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run_pipeline(base_path: str, revised_path: str) -> list:
    """Load → preprocess → detect → match → diff one pair of files."""
    logger.info("Loading  base=%s", base_path)
    base_imgs = load_file(base_path)
    logger.info("Loading  revised=%s", revised_path)
    rev_imgs = load_file(revised_path)
    logger.info("Pages loaded — base: %d, revised: %d", len(base_imgs), len(rev_imgs))

    all_diffs = []

    for page_idx, (b_img, r_img) in enumerate(zip(base_imgs, rev_imgs), start=1):
        logger.debug("── Page %d: preprocessing", page_idx)
        b = preprocess(b_img)
        r = preprocess(r_img)

        base_elements = detect_text(b) + detect_graphics(b) + detect_barcodes(b)
        rev_elements = detect_text(r) + detect_graphics(r) + detect_barcodes(r)
        logger.debug(
            "── Page %d: base elements=%d, revised elements=%d",
            page_idx, len(base_elements), len(rev_elements),
        )

        matches, unmatched_base, unmatched_rev = match(base_elements, rev_elements)
        diffs = detect_differences(matches, unmatched_base, unmatched_rev)
        logger.debug("── Page %d: diffs found=%d", page_idx, len(diffs))
        all_diffs.extend(diffs)

    logger.info("Total diffs: %d", len(all_diffs))
    return all_diffs


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/", tags=["system"], summary="Health check")
def health():
    return {"status": "running"}


async def _process_single_revision(base_path: str, rev: UploadFile) -> ComparisonResult:
    """Handles an individual revised file in a background synchronous thread lock."""
    rev_name = rev.filename or "rev_doc"
    rev_filename = f"{uuid.uuid4()}_{rev_name}"
    rev_path = os.path.join(UPLOAD_DIR, rev_filename)

    # 1. Non-blocking Async I/O Stream
    rev_content = await rev.read()
    
    # Write to disk in a separate thread so node main loop isn't blocked
    def _save_rev():
        with open(rev_path, "wb") as f:
            f.write(rev_content)
    
    await asyncio.to_thread(_save_rev)
    logger.debug("Saved revised → %s", rev_path)

    try:
        # 2. Offload heavy Python CPU/blocking operations
        diffs = await asyncio.to_thread(_run_pipeline, base_path, rev_path)
        diff_list = await asyncio.to_thread(generate_json, diffs)

        html_path = os.path.join(OUTPUT_DIR, f"{rev_filename}.html")
        await asyncio.to_thread(generate_html, diffs, html_path)
        
        logger.info("✔ '%s' — %d diff(s) → report: %s", rev_name, len(diffs), html_path)

        return ComparisonResult(
            revised_file=rev_name,
            status="ok",
            differences=[DiffItem(**d) for d in diff_list],
            html_report=html_path,
        )

    except Exception as exc:
        logger.exception("✘ Pipeline failed for '%s': %s", rev_name, exc)
        return ComparisonResult(
            revised_file=rev_name,
            status="error",
            error=str(exc),
        )

@router.post(
    "/compare/",
    # ── Swagger UI fix ────────────────────────────────────────────────────
    # FastAPI 0.100+ emits OpenAPI 3.1 which uses `contentMediaType` for
    # file fields. The bundled Swagger UI does NOT yet render that as a
    # file-picker; it falls back to a plain text box.
    #
    # Solution: override the requestBody schema via `openapi_extra` so that
    # Swagger UI sees proper `format: binary` (OpenAPI 3.0 style), which it
    # *does* handle correctly.  This has no effect on actual request parsing
    # — FastAPI still reads the multipart form perfectly.
    # ─────────────────────────────────────────────────────────────────────
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "multipart/form-data": {
                    "schema": {
                        "type": "object",
                        "required": ["base", "revised"],
                        "properties": {
                            "base": {
                                "type": "string",
                                "format": "binary",
                                "description": "Base document (PNG / JPEG / PDF)",
                            },
                            "revised": {
                                "type": "array",
                                "items": {"type": "string", "format": "binary"},
                                "description": "One or more revised documents (PNG / JPEG / PDF)",
                            },
                        },
                    }
                }
            },
        }
    },
    response_model=CompareResponse,
    tags=["comparison"],
    summary="Compare base document against one or more revised documents",
)
async def compare(
    base: UploadFile = File(..., description="Base document (PNG / JPEG / PDF)"),
    revised: List[UploadFile] = File(..., description="One or more revised documents"),
) -> CompareResponse:
    logger.info("═══ /compare/ ─ base='%s'  revised_count=%d ═══", base.filename, len(revised))

    # ── Non-blocking Async I/O for Base File ────────────────────────────────
    base_filename = f"{uuid.uuid4()}_{base.filename or 'base_doc'}"
    base_path = os.path.join(UPLOAD_DIR, base_filename)
    
    base_content = await base.read()
    
    def _save_base():
        with open(base_path, "wb") as f:
            f.write(base_content)
    
    await asyncio.to_thread(_save_base)
    logger.debug("Saved base → %s", base_path)

    # ── Launch Threadpool Processing Concurrently ───────────────────────
    tasks = [_process_single_revision(base_path, rev) for rev in revised]
    
    # Executes all processed revisions synchronously together! Wait for them to finish.
    results = await asyncio.gather(*tasks)

    logger.info("═══ /compare/ complete — %d result(s) ═══", len(results))
    return CompareResponse(
        base_file=base.filename or "base_doc",
        total_revised=len(revised),
        results=results,
    )
