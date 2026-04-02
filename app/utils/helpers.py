def bbox_close(b1, b2, threshold=50):
    return abs(b1[0] - b2[0]) < threshold and abs(b1[1] - b2[1]) < threshold