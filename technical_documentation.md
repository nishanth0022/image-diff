# Technical Design Documentation

## Overview
This technical documentation describes the architecture, module definitions, and technology choices driving the highly concurrent, Asynchronous Document & Image Comparison engine.

## Architectural Flow
The module is powered by **FastAPI**. It has been upgraded to utilize an **Asynchronous Parallel Processing** model. 
When a user uploads 1 Base Document and `N` Revised Documents, the API (`app/routes.py`) utilizes `asyncio.gather` and `asyncio.to_thread` to spin up isolated background threads. This allows all `N` documents to be processed completely in parallel without blocking the main event loop, resulting in mathematically scalable speed.

---

## Component Design

### 1. Ingestion Layer (`app.ingestion`)
*   **Role**: Responsible for reading diverse document formats asynchronously and streaming standard numpy buffers into the OpenCV engine.
*   **Module (`loader.py`)**: Identifies the extension. For standard images (PNG, JPEG), utilizes standard OpenCV loading `cv2.imread`. If PDF, uses `fitz` (PyMuPDF) to natively rasterize pages at a strict 2.0x Matrix scale to ensure perfectly crisp geometry without creating static disk artifacts.

### 2. Preprocessing Layer (`app.preprocessing`)
*   **Role**: Prepares the image tensor for optical extraction while maintaining native font sub-pixels for OCR engine integrity.
*   **Module (`preprocess.py`)**: Originally relied on destructive global Deskewing and Global Otsu Binarization. We heavily refactored this to perform **Non-Destructive Grayscaling**. This ensures that digital PDFs with anti-aliased font weights are not pixelated or scrambled before hitting Tesseract.

### 3. Detection Subsystems (`app.detection`)
*   **Role**: Heterogeneously identifies semantic blocks across three independent domains.
*   **`text_detector.py`**: Executes Tesseract. We removed restrictive constraints (like `--psm 6`) allowing the smart segmentation engine to group words into highly cohesive rows using natural spatial relationships.
*   **`graphics_detector.py`**: Discovers non-text outlines/shapes. Because the base image is no longer globally binarized, this module performs its own **Localized Otsu Binarization** mathematically tracking high-contrast contours without damaging the text OCR pipeline.
*   **`barcode_detector.py`**: Parses 1D and QR formats using `pyzbar`. *(Note: Can be easily hot-swapped or augmented with `pylibdmtx` for deep industry 2D Data Matrices).*

### 4. Semantic Comparison Engine (`app.comparison`)
*   **Role**: Maps old data to new data, discovering modifications, removals, additions, and positional drift.
*   **`matcher.py`**: A greedy matching algorithm. It pairs nodes primarily on spatial area Euclidean overlap (`IOU`), and secondary text-similarity sequences.
*   **`diff_engine.py`**: The intelligence center. It relies on the `text_utils.is_ocr_artifact` sub-engine to prevent false-positives. (e.g. It mathematically understands that a 0.95 textual similarity with a tiny pixel jitter is likely an "Optical Artifact" rather than a real business change), preventing the UI from flooding with irrelevant glitch boxes.

### 5. Render & UI Layer (`app.reporting` and `streamlit_app.py`)
*   **Role**: Visualizes the engine's JSON matrices.
*   **Implementation**: A Streamlit UI captures user input and physically transmits multi-part binary payloads over HTTP POST to the backend FastApi service. When results return, the frontend uses native `Pillow ImageDraw` bindings to perfectly map the backend (Red, Green, Yellow) boundaries onto the visual display canvas. 

---

## Technology Stack Rationale
1.  **FastAPI**: Provides native internal `asyncio` loop handling, ensuring background thread pooling for heavy CPU algorithms.
2.  **OpenCV**: Chosen for lightning fast C++ tensor processing (contouring, localized binarization).
3.  **PyTesseract**: Robust text-extraction engine requiring minimal system overhead.
4.  **PyMuPDF (`fitz`)**: Natively natively compiled extension. Vastly outperforms older wrappers like `pdf2image` and completely circumvents the need for massive `Poppler` C-binary installations on Windows.
