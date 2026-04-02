import difflib

def calculate_iou(boxA, boxB):
    # box format: (x_min, y_min, x_max, y_max)
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    interArea = max(0, xB - xA + 1) * max(0, yB - yA + 1)
    
    if interArea == 0:
        return 0.0
        
    boxAArea = (boxA[2] - boxA[0] + 1) * (boxA[3] - boxA[1] + 1)
    boxBArea = (boxB[2] - boxB[0] + 1) * (boxB[3] - boxB[1] + 1)
    
    iou = interArea / float(boxAArea + boxBArea - interArea)
    return iou

def match(base_elements, rev_elements):
    matches = []
    unmatched_base = base_elements.copy()
    unmatched_rev = rev_elements.copy()
    
    scores = []
    
    for i, b in enumerate(base_elements):
        for j, r in enumerate(rev_elements):
            if b.element_type != r.element_type:
                continue
            
            # Text similarity
            text_sim = 1.0
            if b.element_type == "text":
                text_sim = difflib.SequenceMatcher(None, str(b.value), str(r.value)).ratio()
            
            # IoU
            iou_score = calculate_iou(b.bbox, r.bbox)
            
            # A potential match must have reasonable text similarity OR sit in the exact same spot
            if text_sim > 0.6 or iou_score > 0.3:
                final_score = text_sim * 0.7 + iou_score * 0.3
                scores.append((final_score, i, j, b, r))
                
    # Sort all potential matches by highest score first
    scores.sort(key=lambda x: x[0], reverse=True)
    
    matched_base_idx = set()
    matched_rev_idx = set()
    
    for score, i, j, b, r in scores:
        if i in matched_base_idx or j in matched_rev_idx:
            continue
            
        matches.append((b, r))
        matched_base_idx.add(i)
        matched_rev_idx.add(j)
        
        if b in unmatched_base: unmatched_base.remove(b)
        if r in unmatched_rev: unmatched_rev.remove(r)

    return matches, unmatched_base, unmatched_rev