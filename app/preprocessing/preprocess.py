import cv2
import numpy as np

def deskew(img):
    coords = np.column_stack(np.where(img > 0))
    if len(coords) == 0:
        return img
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
        
    if abs(angle) < 0.5:
        return img
        
    (h, w) = img.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return rotated

def preprocess(img):
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Deskew (invert to find text pixels first)
    inverted = cv2.bitwise_not(gray)
    deskewed_inverted = deskew(inverted)
    gray_deskewed = cv2.bitwise_not(deskewed_inverted)
    
    # Return the clean deskewed grayscale directly! 
    # Do NOT apply median blurring or Otsu thresholding here as it destroys crisp digital fonts.
    # Tesseract's internal Leptonica engine handles thresholding optimally.
    return gray_deskewed