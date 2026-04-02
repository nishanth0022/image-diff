import pytesseract
import logging
import shutil
import os
import sys
from app.models.schemas import Element

logger = logging.getLogger("app.detection")

_TESSERACT_AVAILABLE = False
if shutil.which("tesseract"):
    try:
        pytesseract.get_tesseract_version()
        _TESSERACT_AVAILABLE = True
    except Exception:
        pass

if not _TESSERACT_AVAILABLE and sys.platform == "win32":
    for path in [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        r"C:\Tesseract-OCR\tesseract.exe",
    ]:
        if os.path.isfile(path):
            pytesseract.pytesseract.tesseract_cmd = path
            try:
                pytesseract.get_tesseract_version()
                _TESSERACT_AVAILABLE = True
                break
            except Exception:
                continue

if not _TESSERACT_AVAILABLE:
    logger.warning("Tesseract OCR is not installed or not in PATH. Text detection will be skipped.")

def detect_text(img):
    if not _TESSERACT_AVAILABLE:
        return []

    try:
        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
    except Exception as e:
        logger.warning(f"Tesseract failed during detection: {e}")
        return []

    raw_words = []
    for i in range(len(data["text"])):
        text = data["text"][i].strip()
        if text:
            raw_words.append({
                "text": text,
                "x": data["left"][i],
                "y": data["top"][i],
                "w": data["width"][i],
                "h": data["height"][i]
            })

    if not raw_words:
        return []

    # Sort primarily by approximate Y coordinate (binning by 10 pixels to group nearby rows), then by X
    raw_words.sort(key=lambda w: (w["y"] // 10, w["x"]))

    lines = []
    current_line = [raw_words[0]]
    
    for word in raw_words[1:]:
        # If the Y-coordinate of this word is close to the average Y of the current line,
        # it is part of the same line/row. (Tolerance: half the average height)
        avg_y = sum(w["y"] for w in current_line) / len(current_line)
        avg_h = sum(w["h"] for w in current_line) / len(current_line)
        
        if abs(word["y"] - avg_y) < (avg_h * 0.5):
            current_line.append(word)
        else:
            lines.append(current_line)
            current_line = [word]
            
    if current_line:
        lines.append(current_line)
        
    elements = []
    for line_words in lines:
        # Enforce strict left-to-right ordering within the grouped row
        line_words.sort(key=lambda w: w["x"])
        line_text = " ".join(w["text"] for w in line_words)
        
        x_min = min(w["x"] for w in line_words)
        y_min = min(w["y"] for w in line_words)
        x_max = max(w["x"] + w["w"] for w in line_words)
        y_max = max(w["y"] + w["h"] for w in line_words)
        
        elements.append(Element("text", (x_min, y_min, x_max, y_max), line_text))

    return elements