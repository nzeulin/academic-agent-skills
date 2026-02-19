---
name: pdf-highlighted-lines
description: Extract highlighted text from PDF files using PyMuPDF and classify highlight colors by nearest standard color. Use when a user asks to list, export, or analyze highlighted text in PDFs.
---

# Pdf Highlighted Lines

## Overview

Extract highlighted text from PDFs using PyMuPDF. Detects highlight annotations and filled drawing shapes, classifies their colors by nearest standard color, and returns the text covered by highlights. JSON output is supported.

## Quick Start

Use the script to extract highlights:

```bash
python3 scripts/extract_highlighted_lines.py /path/to/file.pdf
```

Emit JSON for programmatic use:

```bash
python3 scripts/extract_highlighted_lines.py /path/to/file.pdf --format json
```

## Workflow

1. Open the PDF with PyMuPDF (`pymupdf`). If unavailable, ask the user to install it.
2. Collect highlight rectangles:
   - Use annotations if present on a page.
   - Otherwise, scan drawing fills for highlight-like rectangles.
3. Classify highlight colors by nearest standard color.
4. Extract text within each highlight rectangle.
5. Merge adjacent highlight rectangles of the same color on the page, then output grouped text.

## Output

- Text format: numbered list with page number, color, and text.
- JSON format: list of objects like:
  - `page` (int)
  - `colors` (list of strings; nearest standard color label)
  - `text` (string)

## Notes

- Colors are assigned by nearest match from a standard color table (e.g., yellow, green, blue, light-blue, red, orange, purple, pink).
