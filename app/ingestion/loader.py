import cv2
import os
import fitz  # PyMuPDF
import numpy as np

def load_file(path):
    images = []

    if path.endswith(".pdf"):
        # Use PyMuPDF instead of pdf2image to avoid Poppler dependency
        doc = fitz.open(path)
        for i in range(len(doc)):
            page = doc[i]
            # Higher DPI (approx 200) for better OCR accuracy
            matrix = fitz.Matrix(2.0, 2.0)
            pix = page.get_pixmap(matrix=matrix)
            
            # Convert PyMuPDF pixmap to OpenCV BGR image format
            img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
            
            # If the image is RGBA (has an alpha channel), convert it to BGR
            if pix.n == 4:
                img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
            # If the image is RGB, convert to BGR (OpenCV's default)
            elif pix.n == 3:
                img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            # If the image is grayscale, convert to BGR
            elif pix.n == 1:
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
                
            images.append(img)
        doc.close()
    else:
        images.append(cv2.imread(path))

    return images