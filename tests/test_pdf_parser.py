from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from thesis_generator.tools import pdf_parser


class DummyDoc:
    def __init__(self, markdown: str) -> None:
        self._markdown = markdown

    def export_to_markdown(self) -> str:
        return self._markdown


def test_parse_pdf_prefers_docling(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    def fake_download(_: str) -> bytes:
        return b"pdf-bytes"

    def fake_docling(path: Path) -> str:
        assert path.suffix == ".pdf"
        return "docling-markdown"

    monkeypatch.setattr(pdf_parser, "_download_pdf", fake_download)
    monkeypatch.setattr(pdf_parser, "_convert_with_docling", fake_docling)

    result = pdf_parser.parse_pdf_from_url("http://example.com/test.pdf")

    assert result == "docling-markdown"


def test_parse_pdf_fallback_on_docling_failure(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    def fake_download(_: str) -> bytes:
        return b"pdf-bytes"

    def fail_docling(_: Path) -> str:
        raise RuntimeError("docling failed")

    def fake_pypdf(path: Path) -> str:
        assert path.exists()
        return "fallback-text"

    monkeypatch.setattr(pdf_parser, "_download_pdf", fake_download)
    monkeypatch.setattr(pdf_parser, "_convert_with_docling", fail_docling)
    monkeypatch.setattr(pdf_parser, "_convert_with_pypdf", fake_pypdf)

    result = pdf_parser.parse_pdf_from_url("http://example.com/test.pdf")

    assert result == "fallback-text"


def test_parse_pdf_raises_on_download_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_download(_: str) -> bytes:
        raise RuntimeError("network")

    monkeypatch.setattr(pdf_parser, "_download_pdf", fail_download)

    with pytest.raises(RuntimeError):
        pdf_parser.parse_pdf_from_url("http://example.com/test.pdf")
