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
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )
    return parser.parse_args()


def intersects(b1, b2):
    x0, y0, x1, y1 = b1
    a0, b0, a1, b1_ = b2
    return not (x1 < a0 or a1 < x0 or y1 < b0 or b1_ < y0)


def extract_lines(page):
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
            lines.append({"text": line_text, "lines": [{"text": line_text, "bbox": bbox}]})
    lines.sort(key=lambda x: (x["lines"][0]["bbox"][1], x["lines"][0]["bbox"][0]))
    return lines


def extract_highlight_text(page, rect):
    text = page.get_text("text", clip=rect).strip()
    if not text:
        return []
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    return lines


def rect_to_tuple(rect):
    return (rect.x0, rect.y0, rect.x1, rect.y1)


def classify_nearest_color(c, color_table):
    if c is None:
        return None
    label, _ = min(
        ((name, dist(c, rgb)) for name, rgb in color_table.items()),
        key=lambda item: item[1],
    )
    return label


def has_unhighlighted_gap_between(lines, upper_y, lower_y):
    for line in lines:
        y0 = line["lines"][0]["bbox"][1]
        y1 = line["lines"][0]["bbox"][3]
        if y0 > lower_y or y1 < upper_y:
            continue
        if line.get("has_unhighlighted_gap"):
            return True
    return False


def has_unhighlighted_after_between(lines, upper_y, lower_y):
    for line in lines:
        y0 = line["lines"][0]["bbox"][1]
        y1 = line["lines"][0]["bbox"][3]
        if y0 > lower_y or y1 < upper_y:
            continue
        if line.get("has_unhighlighted_after"):
            return True
    return False


def should_merge_rects(prev_rect, next_rect, lines):
    prev_height = max(1.0, prev_rect[3] - prev_rect[1])
    y_gap = next_rect[1] - prev_rect[3]
    vertical_overlap = next_rect[1] <= prev_rect[3] and next_rect[3] >= prev_rect[1]
    same_line = vertical_overlap or abs(next_rect[1] - prev_rect[1]) <= prev_height * 0.5

    if same_line:
        x_gap = next_rect[0] - prev_rect[2]
        return x_gap <= max(6.0, prev_height * 0.6)

    if y_gap > max(4.0, prev_height * 0.8):
        return False

    if has_unhighlighted_after_between(lines, prev_rect[1], next_rect[1]):
        return False

    return True


def main():
    args = parse_args()
    pymupdf = require_pymupdf()

    color_table = {
        "yellow": (1.0, 1.0, 0.0),
        "green": (0.0, 1.0, 0.0),
        "blue": (0.0, 1.0, 1.0),
        "light-blue": (0.6, 0.8, 1.0),
        "red": (1.0, 0.0, 0.0),
        "orange": (1.0, 0.6, 0.0),
        "purple": (0.6, 0.2, 0.8),
        "pink": (1.0, 0.6, 0.8),
    }

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
        page_highlights = []
        for h in highlights:
            if h["page"] != pi:
                continue
            label = classify_nearest_color(h["color"], color_table)
            if not label:
                continue
            lines = extract_highlight_text(page, h["rect"])
            if not lines:
                continue
            page_highlights.append(
                {
                    "rect": rect_to_tuple(h["rect"]),
                    "color": label,
                    "lines": lines,
                }
            )

        if not page_highlights:
            continue

        lines = extract_lines(page)
        for line in lines:
            line_rect = line["lines"][0]["bbox"]
            highlighted = False
            intervals = []
            for h in page_highlights:
                if not intersects(line_rect, h["rect"]):
                    continue
                highlighted = True
                x0 = max(line_rect[0], h["rect"][0])
                x1 = min(line_rect[2], h["rect"][2])
                if x1 > x0:
                    intervals.append((x0, x1))
            line["highlighted_any"] = highlighted
            if not highlighted:
                line["has_unhighlighted_gap"] = False
                line["has_unhighlighted_after"] = False
                line["highlighted_max_x"] = None
                continue

            intervals.sort()
            merged = []
            for start, end in intervals:
                if not merged or start > merged[-1][1]:
                    merged.append([start, end])
                else:
                    merged[-1][1] = max(merged[-1][1], end)
            covered = sum(end - start for start, end in merged)
            line_width = max(1.0, line_rect[2] - line_rect[0])
            coverage_ratio = covered / line_width
            highlighted_max_x = max(end for _, end in merged)
            line["highlighted_max_x"] = highlighted_max_x
            line["has_unhighlighted_gap"] = coverage_ratio < 0.95
            line["has_unhighlighted_after"] = (line_rect[2] - highlighted_max_x) > max(
                6.0, line_width * 0.1
            )

        page_highlights.sort(key=lambda h: (h["rect"][1], h["rect"][0]))
        grouped = []
        for item in page_highlights:
            if (
                grouped
                and grouped[-1]["color"] == item["color"]
                and should_merge_rects(grouped[-1]["last_rect"], item["rect"], lines)
            ):
                grouped[-1]["lines"].extend(item["lines"])
                x0, y0, x1, y1 = grouped[-1]["rect"]
                nx0, ny0, nx1, ny1 = item["rect"]
                grouped[-1]["rect"] = (min(x0, nx0), min(y0, ny0), max(x1, nx1), max(y1, ny1))
                grouped[-1]["last_rect"] = item["rect"]
            else:
                item["last_rect"] = item["rect"]
                grouped.append(item)

        for item in grouped:
            text = " ".join(item["lines"])
            output = {
                "page": pi,
                "colors": [item["color"]],
                "text": text,
            }
            key = (output["page"], output["text"])
            if key not in seen:
                seen.add(key)
                results.append(output)

    if args.format == "json":
        print(json.dumps(results, indent=2))
        return

    for i, item in enumerate(results, start=1):
        colors = ", ".join(item["colors"])
        print(f"{i}. Page: {item['page']}, Color: {colors}")
        print(f"\"{item['text']}\"")
        print()


if __name__ == "__main__":
    main()
