#!/usr/bin/env python3
"""
Extract highlighted lines or enumerated comments from a PDF.

Uses PyMuPDF (pymupdf) to detect highlight annotations or filled drawing shapes
and maps them to enumerated comments like "1. ..." on each page.
"""

import argparse
import json
import re
import sys
from math import sqrt


def require_pymupdf():
    try:
        import pymupdf  # type: ignore
        return pymupdf
    except Exception:
        print("PyMuPDF not available. Install with: pip install pymupdf", file=sys.stderr)
        sys.exit(2)


def dist(c1, c2):
    return sqrt(sum((a - b) ** 2 for a, b in zip(c1, c2)))


def parse_args():
    parser = argparse.ArgumentParser(
        description="Extract highlighted lines/comments from a PDF using PyMuPDF."
    )
    parser.add_argument("pdf", help="Path to PDF file")
    parser.add_argument(
        "--colors",
        nargs="+",
        default=["yellow", "light-blue"],
        help="Highlight colors to include: yellow, light-blue",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )
    parser.add_argument(
        "--yellow-threshold",
        type=float,
        default=0.35,
        help="RGB distance threshold for yellow",
    )
    parser.add_argument(
        "--light-blue-threshold",
        type=float,
        default=0.35,
        help="RGB distance threshold for light blue",
    )
    return parser.parse_args()


def is_color(c, target, threshold):
    return c is not None and dist(c, target) <= threshold


def intersects(b1, b2):
    x0, y0, x1, y1 = b1
    a0, b0, a1, b1_ = b2
    return not (x1 < a0 or a1 < x0 or y1 < b0 or b1_ < y0)


def extract_comments(page):
    text_dict = page.get_text("dict")
    lines = []
    for block in text_dict.get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            spans = line.get("spans", [])
            line_text = "".join(s.get("text", "") for s in spans).strip()
            if not line_text:
                continue
            bbox = line.get("bbox")
            lines.append({"text": line_text, "bbox": bbox})
    lines.sort(key=lambda x: (x["bbox"][1], x["bbox"][0]))

    comments = []
    current = None
    for ln in lines:
        m = re.match(r"^(\d+)\.\s*(.*)$", ln["text"])
        if m:
            if current:
                comments.append(current)
            num = m.group(1)
            current = {"num": num, "lines": [ln], "text": ln["text"]}
        else:
            if current:
                current["lines"].append(ln)
                current["text"] += " " + ln["text"]
    if current:
        comments.append(current)
    return comments


def extract_highlight_text(page, rect):
    text = page.get_text("text", clip=rect).strip()
    if not text:
        return []
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    return lines


def main():
    args = parse_args()
    pymupdf = require_pymupdf()

    target_colors = set(args.colors)
    yellow_rgb = (1.0, 1.0, 0.0)
    light_blue_rgb = (0.6, 0.8, 1.0)

    doc = pymupdf.open(args.pdf)
    highlights = []

    for pi, page in enumerate(doc, start=1):
        # Prefer annotations if present
        annots = list(page.annots() or [])
        for a in annots:
            colors = getattr(a, "colors", None)
            c = None
            if colors and colors.get("fill"):
                c = colors.get("fill")
            elif colors and colors.get("stroke"):
                c = colors.get("stroke")
            if c:
                highlights.append({"page": pi, "rect": a.rect, "color": c})

        # Fallback to drawings if no annotations
        if not annots:
            for d in page.get_drawings():
                fill = d.get("fill")
                rect = d.get("rect")
                if fill and rect:
                    highlights.append({"page": pi, "rect": rect, "color": fill})

    results = []
    seen = set()
    for pi, page in enumerate(doc, start=1):
        comments = extract_comments(page)
        for c in comments:
            c["page"] = pi
            c["highlight"] = set()
            for h in highlights:
                if h["page"] != pi:
                    continue
                for ln in c["lines"]:
                    if intersects(ln["bbox"], h["rect"]):
                        if "yellow" in target_colors and is_color(
                            h["color"], yellow_rgb, args.yellow_threshold
                        ):
                            c["highlight"].add("yellow")
                        if "light-blue" in target_colors and is_color(
                            h["color"], light_blue_rgb, args.light_blue_threshold
                        ):
                            c["highlight"].add("light blue")
                        break

            if c["highlight"]:
                item = {
                    "page": c["page"],
                    "comment": c["num"],
                    "colors": sorted(c["highlight"]),
                    "text": c["text"],
                }
                key = (item["page"], item["comment"], item["text"])
                if key not in seen:
                    seen.add(key)
                    results.append(item)

        # Add any highlighted lines that are not part of enumerated comments
        for h in highlights:
            if h["page"] != pi:
                continue
            matched = False
            for c in comments:
                for ln in c["lines"]:
                    if intersects(ln["bbox"], h["rect"]):
                        matched = True
                        break
                if matched:
                    break
            if matched:
                continue

            colors = []
            if "yellow" in target_colors and is_color(
                h["color"], yellow_rgb, args.yellow_threshold
            ):
                colors.append("yellow")
            if "light-blue" in target_colors and is_color(
                h["color"], light_blue_rgb, args.light_blue_threshold
            ):
                colors.append("light blue")
            if not colors:
                continue

            for line in extract_highlight_text(page, h["rect"]):
                item = {
                    "page": pi,
                    "comment": None,
                    "colors": colors,
                    "text": line,
                }
                key = (item["page"], item["comment"], item["text"])
                if key not in seen:
                    seen.add(key)
                    results.append(item)

    if args.format == "json":
        print(json.dumps(results, indent=2))
        return

    for item in results:
        colors = ", ".join(item["colors"])
        comment = item["comment"] if item["comment"] is not None else "n/a"
        print(f"page {item['page']} comment {comment} colors {colors}")
        print(item["text"])
        print("---")


if __name__ == "__main__":
    main()
