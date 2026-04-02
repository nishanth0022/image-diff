from app.models.schemas import Difference
from app.utils.text_utils import is_ocr_artifact, normalize_text

def is_micro_shift(boxA, boxB, tolerance=5):
    # Returns True if the boxes are very close in position and size
    if boxA is None or boxB is None:
        return False
        
    return (abs(boxA[0] - boxB[0]) <= tolerance and
            abs(boxA[1] - boxB[1]) <= tolerance and
            abs(boxA[2] - boxB[2]) <= tolerance and
            abs(boxA[3] - boxB[3]) <= tolerance)

def detect_differences(matches, unmatched_base, unmatched_rev):
    diffs = []

    # modified or shifted
    for b, r in matches:
        if b.value != r.value:
            if b.element_type == "text" and is_ocr_artifact(str(b.value), str(r.value)):
                # False positive: It is just an OCR artifact.
                # However, the bounding box might still have shifted
                if b.bbox != r.bbox and not is_micro_shift(b.bbox, r.bbox):
                    clean_val = normalize_text(str(b.value))
                    diffs.append(Difference(b.element_type, "shift", clean_val, clean_val, b.bbox))
                continue
                
            # Genuine modification
            diffs.append(Difference(b.element_type, "modified", b.value, r.value, b.bbox))
        elif b.bbox != r.bbox:
            # Text is strictly identical but position changed
            if is_micro_shift(b.bbox, r.bbox):
                continue
            else:
                diffs.append(Difference(b.element_type, "shift", b.value, r.value, b.bbox))

    # removed / missing row
    for b in unmatched_base:
        diffs.append(Difference(b.element_type, "removed", b.value, None, b.bbox))

    # added / new row
    for r in unmatched_rev:
        diffs.append(Difference(r.element_type, "added", None, r.value, r.bbox))

    return diffs