import cv2
from app.models.schemas import Element

def detect_graphics(img):
    contours, _ = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    elements = []

    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)

        if w > 80 and h > 80:
            elements.append(Element("graphic", (x, y, x+w, y+h), "shape"))

    return elements