"""
schemas.py — data models for the Image Comparison pipeline.

Two layers:
  1. Internal plain-Python dataclasses (Element, Difference) — used by the
     detection / matching / diff-engine modules.
  2. Pydantic response models (DiffItem, ComparisonResult, CompareResponse) —
     used by FastAPI to validate and document the /compare/ endpoint response.
"""

from __future__ import annotations

from typing import Any, List, Optional

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Layer 1 – internal pipeline dataclasses
# ---------------------------------------------------------------------------

class Element:
    """A detected element (text block or graphic region) on a document page."""

    def __init__(self, element_type: str, bbox: tuple, value: Any) -> None:
        self.element_type = element_type  # "text" | "graphic" | "barcode" …
        self.bbox = bbox                  # (x1, y1, x2, y2)
        self.value = value                # OCR string, barcode payload, etc.


class Difference:
    """A single detected difference between base and revised elements."""

    def __init__(
        self,
        element_type: str,
        change_type: str,
        base_value: Any,
        revised_value: Any,
        bbox: Any,
        revised_bbox: Any = None,
    ) -> None:
        self.element_type = element_type    # "text" | "graphic" …
        self.change_type = change_type      # "modified" | "shift" | "removed" | "added"
        self.base_value = base_value
        self.revised_value = revised_value
        self.bbox = bbox
        self.revised_bbox = revised_bbox


# ---------------------------------------------------------------------------
# Layer 2 – Pydantic API response models
# ---------------------------------------------------------------------------

class DiffItem(BaseModel):
    """One diff entry as returned in the API response."""
    type: str
    change: str
    base: Optional[str] = None
    revised: Optional[str] = None
    bbox: Optional[Any] = None
    revised_bbox: Optional[Any] = None


class ComparisonResult(BaseModel):
    """Result for a single (base, revised) file pair."""
    revised_file: str
    status: str                          # "ok" | "error"
    differences: List[DiffItem] = []
    html_report: Optional[str] = None
    error: Optional[str] = None


class CompareResponse(BaseModel):
    """Top-level response returned by POST /compare/."""
    base_file: str
    total_revised: int
    results: List[ComparisonResult]