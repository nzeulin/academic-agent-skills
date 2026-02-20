#!/usr/bin/env python3
"""
Extract comments from a PDF and return referenced text.

Uses PyMuPDF (pymupdf) to read annotations. For highlight annotations,
extract referenced text using quadpoints to match the highlighted span.
"""

import argparse
import json
import sys


def require_pymupdf():
    try:
        import pymupdf  # type: ignore
        return pymupdf
    except Exception:
        print("PyMuPDF not available. Install with: pip install pymupdf", file=sys.stderr)
        sys.exit(2)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Extract comments from a PDF using PyMuPDF."
    )
    parser.add_argument("pdf", help="Path to PDF file")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )
    return parser.parse_args()


def quad_rects(pymupdf, vertices):
    rects = []
    if not vertices:
        return rects
    for i in range(0, len(vertices), 4):
        quad = vertices[i : i + 4]
        xs = [p[0] for p in quad]
        ys = [p[1] for p in quad]
        rects.append(pymupdf.Rect(min(xs), min(ys), max(xs), max(ys)))
    rects.sort(key=lambda r: (r.y0, r.x0))
    return rects


def extract_reference(page, annot, pymupdf):
    vertices = getattr(annot, "vertices", None)
    rects = quad_rects(pymupdf, vertices)
    if not rects:
        rects = [annot.rect]

    parts = []
    for rect in rects:
        text = page.get_text("text", clip=rect)
        if text:
            parts.append(text.rstrip())

    return "\n".join(parts).rstrip()


def main():
    args = parse_args()
    pymupdf = require_pymupdf()

    doc = pymupdf.open(args.pdf)
    results = []

    for pi, page in enumerate(doc, start=1):
        annots = list(page.annots() or [])
        for annot in annots:
            info = getattr(annot, "info", {}) or {}
            content = info.get("content") or ""
            if not content:
                continue

            reference = extract_reference(page, annot, pymupdf)
            results.append(
                {
                    "page": pi,
                    "reference": reference,
                    "text": content,
                }
            )

    if args.format == "json":
        print(json.dumps(results, indent=2))
        return

    for i, item in enumerate(results, start=1):
        print(f"{i}. Page: {item['page']}, Reference: \"{item['reference']}\"")
        print(f"Comment: \"{item['text']}\"")
        if i != len(results):
            print()


if __name__ == "__main__":
    main()
