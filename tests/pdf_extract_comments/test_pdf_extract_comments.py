from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture(scope="module")
def fixtures_dir() -> Path:
    return Path(__file__).resolve().parent


@pytest.fixture(scope="module")
def repo_root(fixtures_dir: Path) -> Path:
    return fixtures_dir.parents[1]


@pytest.fixture(scope="module")
def script_path(repo_root: Path) -> Path:
    return repo_root / "skills/pdf-extract-comments/scripts/extract_comments.py"


def _run_script(script_path: Path, pdf_path: Path, output_format: str) -> str:
    pytest.importorskip("pymupdf")
    result = subprocess.run(
        [
            sys.executable,
            str(script_path),
            str(pdf_path),
            "--format",
            output_format,
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def test_output_text_matches_expected(fixtures_dir: Path, script_path: Path) -> None:
    pdf_path = fixtures_dir / "input_okular.pdf"
    expected_path = fixtures_dir / "output_text.txt"

    actual = _run_script(script_path, pdf_path, "text").strip()
    expected = expected_path.read_text().strip()

    assert actual == expected


def test_output_json_matches_expected(fixtures_dir: Path, script_path: Path) -> None:
    pdf_path = fixtures_dir / "input_edge.pdf"
    expected_path = fixtures_dir / "output_json.json"

    actual = _run_script(script_path, pdf_path, "json")
    expected = expected_path.read_text()

    assert json.loads(actual) == json.loads(expected)
