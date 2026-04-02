from pyzbar.pyzbar import decode
from app.models.schemas import Element

import os
os.environ["PATH"] += r";C:\Program Files\ZBar\bin"

import logging
logger = logging.getLogger("app.detection.barcode")

def detect_barcodes(img):
    try:
        results = decode(img)
    except Exception as e:
        logger.warning(f"Barcode decoding failed. ZBar may not be installed. {e}")
        return []

    elements = []
    for r in results:
        x, y, w, h = r.rect
        value = r.data.decode("utf-8")
        elements.append(Element("barcode", (x, y, x+w, y+h), value))

    return elements