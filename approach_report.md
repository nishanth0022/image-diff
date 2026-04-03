# Approach Overview & Trade-off Report

## Background
The document comparison pipeline is designed to analyze base versus revised versions of complex multimodal files (invoices, forms, blueprints) and emit highly structured outputs targeting actionable business logic. This is typically an error-prone task due to OCR misreads, scan deterioration, format shifts, and trivial layout mutations. 

## Approach Strategy

Our solution relies on a heterogeneous strategy shifting away from raw pixel-based subtraction (e.g. `ImageChops.difference`) to a multi-stage **Object Mapping Paradigm**. 
First, we ingest the files into spatial units (Text Rows, Graphics, Barcodes). Instead of mapping every piece of text randomly, we group text algorithmically utilizing bounding box Y-coordinate tolerances to assemble natural table rows.

Then, the Comparison Engine utilizes a sophisticated greedy aligner. Text strings are scored simultaneously on **positional containment (IoU ratio)** and **textual similarity (Levenshtein distance)**. By evaluating elements spatially rather than structurally, we catch changes gracefully.

Finally, differences run through an intercept filtering module (`text_utils.py`) to silence the most prevalent issues in computer vision document pairing.

## Advantages and Capabilities
1. **Semantic Extraction**: We identify precise strings changing (e.g., "1300" -> "1500") rather than highlighting a large bounding box anomaly.
2. **Tabular Robustness**: Row-building protects columns from matching incorrectly on the X-axis. Missing rows are identified elegantly as a "Removed Row", rather than creating chaotic text mutations.
3. **No-noise Outputs**: Micro-shifts (rendering shifts underneath 5 pixels) and common optical artifact typos (e.g., `l` vs `I`) are mathematically nullified automatically.

## Limitations & Trade-offs

1. **Unstructured Machine Learning Reliance**: The tool relies strictly on heuristics instead of an end-to-end trained AI transformer model (like LayoutLM). 
   * *Trade-off*: Performance is significantly faster and doesn't require a GPU, but complex overlapping graphics or aggressively nested table columns might bleed into each other without true semantic understanding of visual layout borders. 

2. **Strict Positional Fallbacks**:
   * *Limitation*: If a paragraph moves drastically to the opposite side of the page (beyond intersection constraints), it will register as a full Removal on the left and a full Addition on the right, rather than recognizing the paragraph itself moved. 

3. **OCR Configuration Bottlenecks**:
   * *Trade-off*: Currently, Tesseract is configured tightly to `--psm 6` which expects unified text blocks ideal for 90% of business formats (invoices, letters). However, if an engineer uploads a scattered architectural CAD diagram, PSM 6 will perform significantly worse than a sparser auto-detect mode. 

By bounding these trade-offs mathematically, the pipeline stays predictable and fully observable on modern digital documentation infrastructures.
