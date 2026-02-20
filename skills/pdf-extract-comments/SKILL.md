---
name: pdf-extract-comments
description: Extract comments/annotation text and their referenced spans from PDF files using PyMuPDF. Use when a user asks to list, export, or analyze PDF comments, notes, or annotations (including highlighted text comments).
---

# Pdf Extract Comments

## Overview

Extract PDF comments (annotation contents) and the referenced text spans. Supports text and JSON outputs.

## Quick Start

Extract comments as text:

```bash
python3 scripts/extract_comments.py /path/to/file.pdf
```

Extract comments as JSON:

```bash
python3 scripts/extract_comments.py /path/to/file.pdf --format json
```

## Workflow

1. Open the PDF with PyMuPDF (`pymupdf`). If unavailable, ask the user to install it.
2. Iterate annotations on each page, skipping those without comment content.
3. For highlight annotations, use quadpoints to extract the referenced text span.
4. Output results as text or JSON.

## Output

- Text format: numbered list with page number, reference text, and comment content.
- JSON format: list of objects. Keys: `page` (int), `reference` (string), `text` (string).
