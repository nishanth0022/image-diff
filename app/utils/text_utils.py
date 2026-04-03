import difflib
import re

def normalize_text(text: str) -> str:
    """Lowercase and normalize whitespace/spacing."""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def normalize_for_ocr(text: str) -> str:
    """Normalize common OCR confusions heavily for artifact checking."""
    text = normalize_text(text)
    # Target typical false positive swaps
    text = re.sub(r'[ıl\[\]1\|]', '1', text)
    text = re.sub(r'[o0]', '0', text)
    text = re.sub(r'rn', 'm', text)
    return text

def is_ocr_artifact(base: str, rev: str, threshold: float = 0.95) -> bool:
    norm_b = normalize_text(base)
    norm_r = normalize_text(rev)
    
    # 1. Exact normalized match
    if norm_b == norm_r:
        return True
        
    # 2. Match after aggressive OCR-confusion wiping (l->1, o->0, etc)
    ocr_b = normalize_for_ocr(base)
    ocr_r = normalize_for_ocr(rev)
    if ocr_b == ocr_r:
        return True
        
    # 3. Fuzzy match check
    sim = difflib.SequenceMatcher(None, norm_b, norm_r).ratio()
    if sim > threshold:
        # Safeguard 1: Guarantee we aren't masking numerical changes!
        nums_b = re.findall(r'\d+', norm_b)
        nums_r = re.findall(r'\d+', norm_r)
        if nums_b != nums_r:
            return False
            
        # Safeguard 2: Guarantee we aren't masking 1-letter shifts like 'Product B' vs 'Product C'
        # A single letter shift in short strings creates a falsely high difflib ratio.
        words_b = norm_b.split()
        words_r = norm_r.split()
        if len(words_b) == len(words_r):
            for wb, wr in zip(words_b, words_r):
                if wb != wr and len(wb) == 1 and len(wr) == 1:
                    if wb.isalpha() and wr.isalpha():
                        return False
                        
        return True
        
    return False
