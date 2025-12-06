from __future__ import annotations

from pathlib import Path

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


def test_parse_pdf_preserves_headings_and_tables(monkeypatch: pytest.MonkeyPatch) -> None:
    markdown = "# Introduction\n\n| Col1 | Col2 |\n| --- | --- |\n| a | b |"

    def fake_download(_: str) -> bytes:
        return b"pdf-bytes"

    def fake_docling(_: Path) -> str:
        return markdown

    monkeypatch.setattr(pdf_parser, "_download_pdf", fake_download)
    monkeypatch.setattr(pdf_parser, "_convert_with_docling", fake_docling)

    result = pdf_parser.parse_pdf_from_url("http://example.com/complex.pdf")

    assert "# Introduction" in result
    assert "| Col1 | Col2 |" in result


def test_parse_pdf_fallback_on_docling_failure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
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


def test_unstructured_fallback_when_docling_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    sequence: list[str] = []

    def fake_download(_: str) -> bytes:
        return b"pdf-bytes"

    def fail_docling(_: Path) -> str:
        sequence.append("docling")
        raise RuntimeError("docling failed")

    def fake_unstructured(path: Path) -> str:
        sequence.append("unstructured")
        assert path.exists()
        return "unstructured-text"

    monkeypatch.setattr(pdf_parser, "_download_pdf", fake_download)
    monkeypatch.setattr(pdf_parser, "_convert_with_docling", fail_docling)
    monkeypatch.setattr(pdf_parser, "_convert_with_unstructured", fake_unstructured)

    result = pdf_parser.parse_pdf_from_url("http://example.com/test.pdf")

    assert result == "unstructured-text"
    assert sequence == ["docling", "unstructured"]


def test_pypdf_fallback_when_other_parsers_fail(monkeypatch: pytest.MonkeyPatch) -> None:
    sequence: list[str] = []

    def fake_download(_: str) -> bytes:
        return b"pdf-bytes"

    def fail_docling(_: Path) -> str:
        sequence.append("docling")
        raise RuntimeError("docling failed")

    def fail_unstructured(_: Path) -> str:
        sequence.append("unstructured")
        raise RuntimeError("unstructured failed")

    def fake_pypdf(path: Path) -> str:
        sequence.append("pypdf")
        assert path.exists()
        return "pypdf-text"

    monkeypatch.setattr(pdf_parser, "_download_pdf", fake_download)
    monkeypatch.setattr(pdf_parser, "_convert_with_docling", fail_docling)
    monkeypatch.setattr(pdf_parser, "_convert_with_unstructured", fail_unstructured)
    monkeypatch.setattr(pdf_parser, "_convert_with_pypdf", fake_pypdf)

    result = pdf_parser.parse_pdf_from_url("http://example.com/test.pdf")

    assert result == "pypdf-text"
    assert sequence == ["docling", "unstructured", "pypdf"]


def test_parse_pdf_raises_on_download_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_download(_: str) -> bytes:
        raise RuntimeError("network")

    monkeypatch.setattr(pdf_parser, "_download_pdf", fail_download)

    with pytest.raises(RuntimeError) as excinfo:
        pdf_parser.parse_pdf_from_url("http://example.com/test.pdf")

    assert "http://example.com/test.pdf" in str(excinfo.value)
