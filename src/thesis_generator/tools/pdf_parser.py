from __future__ import annotations

import tempfile
from pathlib import Path

import requests

from thesis_generator.security import mask_pii

def _download_pdf(url: str) -> bytes:
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    return response.content


def _convert_with_docling(path: Path) -> str:
    try:
        from docling.document_converter import DocumentConverter
    except Exception as exc:  # pragma: no cover - executed in runtime if missing
        raise ImportError("docling is not available") from exc

    converter = DocumentConverter()
    result = converter.convert(str(path))
    document = getattr(result, "document", None)
    if document is None:
        raise RuntimeError("Docling conversion returned no document")

    if hasattr(document, "export_to_markdown"):
        return document.export_to_markdown()

    if hasattr(document, "as_markdown"):
        return document.as_markdown()

    raise RuntimeError("Docling document does not support markdown export")


def _convert_with_unstructured(path: Path) -> str:
    try:
        from unstructured.partition.pdf import partition_pdf
    except Exception as exc:  # pragma: no cover - optional dependency
        raise ImportError("unstructured is not available") from exc

    elements = partition_pdf(str(path))
    if not elements:
        raise RuntimeError("Unstructured returned no elements")

    parts = [getattr(element, "text", "").strip() for element in elements]
    text = "\n\n".join(part for part in parts if part)
    if not text:
        raise RuntimeError("Unstructured returned empty text")
    return text


def _convert_with_pypdf(path: Path) -> str:
    from PyPDF2 import PdfReader

    reader = PdfReader(str(path))
    pages = [page.extract_text() or "" for page in reader.pages]
    text = "\n\n".join(pages).strip()
    if not text:
        raise RuntimeError("PyPDF2 failed to extract text")
    return text


def parse_pdf_from_url(url: str) -> str:
    """Download a PDF and convert it to Markdown with fallbacks."""

    try:
        pdf_bytes = _download_pdf(url)
    except Exception as exc:
        raise RuntimeError(f"Failed to download PDF from {url}") from exc

    with tempfile.NamedTemporaryFile(delete=True, suffix=".pdf") as tmp:
        tmp.write(pdf_bytes)
        tmp.flush()
        pdf_path = Path(tmp.name)

        errors: list[str] = []
        for converter in (_convert_with_docling, _convert_with_unstructured, _convert_with_pypdf):
            try:
                return mask_pii(converter(pdf_path))
            except Exception as exc:  # pragma: no cover - aggregated for error reporting
                errors.append(str(exc))
                continue

        raise RuntimeError("Failed to parse PDF with any parser: " + "; ".join(errors))


__all__ = ["parse_pdf_from_url"]
