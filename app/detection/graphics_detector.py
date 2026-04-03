import cv2
from app.models.schemas import Element

def detect_graphics(img):
    # Invert and apply robust internal thresholding so OpenCV can detect graphical shapes on grayscale
    inverted = cv2.bitwise_not(img)
    _, binary = cv2.threshold(inverted, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    elements = []

    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)

        if w > 80 and h > 80:
            elements.append(Element("graphic", (x, y, x+w, y+h), "shape"))

    return elements