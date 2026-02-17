---
name: pdf-highlighted-lines
description: Extract highlighted lines or enumerated comments from PDF files, including color-specific filters (e.g., yellow or light blue) using PyMuPDF. Use when a user asks to list, export, or analyze highlighted text/comments in PDFs or to filter highlights by color.
---

# Pdf Highlighted Lines

## Overview

Extract highlighted text and numbered comments from PDFs, with optional color filtering (yellow/light blue). Uses PyMuPDF for reliable annotation and drawing-based highlight detection.

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

## Workflow

1. Open the PDF with PyMuPDF (`pymupdf`). If unavailable, ask the user to install it.
2. Gather highlight regions:
   - Prefer annotations (`page.annots()`), but if absent, scan drawings (`page.get_drawings()`) for highlight fills.
3. Extract enumerated comments:
   - Parse page text lines and group blocks starting with `^\d+\.` into comments.
4. Assign highlight colors by rectangle intersection between comment lines and highlight regions.
5. Filter by requested colors (yellow/light blue) and print results.

## Notes

- Colors are compared with an RGB distance threshold. If a PDF uses unusual highlight colors, adjust `--yellow-threshold` or `--light-blue-threshold`.
- If the document uses highlight annotations instead of drawing fills, the script still detects them.
