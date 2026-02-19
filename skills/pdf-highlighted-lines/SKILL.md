---
name: pdf-highlighted-lines
description: Extract highlighted text from PDF files with optional color filters (yellow/green/blue) using PyMuPDF. Use when a user asks to list, export, or analyze highlighted text in PDFs or to filter highlights by color.
---

# Pdf Highlighted Lines

## Overview

Extract highlighted text from PDFs using PyMuPDF. Detects highlight annotations and filled drawing shapes, classifies their colors (yellow/green/blue), and returns the text covered by highlights. Optional color filtering and JSON output are supported.

## Quick Start

Use the script to extract highlights:

```bash
python3 scripts/extract_highlighted_lines.py /path/to/file.pdf
```

Filter by color:

```bash
python3 scripts/extract_highlighted_lines.py /path/to/file.pdf --colors yellow light-blue
```

Emit JSON for programmatic use:

```bash
python3 scripts/extract_highlighted_lines.py /path/to/file.pdf --format json
```

Adjust color matching sensitivity:

```bash
python3 scripts/extract_highlighted_lines.py /path/to/file.pdf --color-threshold 0.25
```

## Workflow

1. Open the PDF with PyMuPDF (`pymupdf`). If unavailable, ask the user to install it.
2. Collect highlight rectangles:
   - Use annotations if present on a page.
   - Otherwise, scan drawing fills for highlight-like rectangles.
3. Classify highlight colors using RGB distance and `--color-threshold`.
4. Extract text within each highlight rectangle.
5. Merge adjacent highlight rectangles of the same color on the page, then output grouped text.

## Output

- Text format: numbered list with page number, color, and text.
- JSON format: list of objects like:
  - `page` (int)
  - `colors` (list of strings; `light-blue` normalizes to `blue`)
  - `text` (string)

## Notes

- `--colors` accepts `yellow`, `green`, `blue`, `light-blue`, or `all` (default).
- Color detection uses a single `--color-threshold` (default `0.35`) for RGB distance.
- If a PDF uses unusual highlight colors, reduce the threshold to make matching stricter.
