from __future__ import annotations

import uuid
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Chunk:
    """Lightweight document representation similar to LangChain's Document."""

    page_content: str
    metadata: dict[str, Any]


@dataclass
class SearchResult:
    """Return type for search results with parent-child linkage."""

    chunk: Chunk
    parent: Chunk
    score: float


@dataclass
class SourceSection:
    heading: str
    content: str


@dataclass
class SourceDocument:
    title: str
    year: int | None = None
    citations: int | None = None
    authors: list[str] = field(default_factory=list)
    sections: list[SourceSection] = field(default_factory=list)


class ParentChildVectorStore:
    """In-memory vector-like store that tracks parent/child chunks."""

    def __init__(self, uri: str) -> None:
        self.uri = uri
        self.parents: dict[str, Chunk] = {}
        self.children: list[Chunk] = []

    def add_section(self, parent: Chunk, children: Sequence[Chunk]) -> None:
        self.parents[parent.metadata["id"]] = parent
        self.children.extend(children)

    def search(
        self,
        query: str,
        filters: Mapping[str, Any] | None = None,
        k: int = 5,
    ) -> list[SearchResult]:
        filtered_children = [
            child for child in self.children if _passes_filters(child.metadata, filters)
        ]
        scored = [
            (self._score(query, child.page_content), child) for child in filtered_children
        ]
        scored.sort(key=lambda pair: pair[0], reverse=True)
        top = scored[:k]
        return [
            SearchResult(
                chunk=child,
                parent=self.parents[child.metadata["parent_id"]],
                score=score,
            )
            for score, child in top
            if score > 0
        ]

    @staticmethod
    def _score(query: str, text: str) -> float:
        query_terms = set(query.lower().split())
        if not query_terms:
            return 0
        text_terms = text.lower().split()
        overlap = sum(1 for term in text_terms if term in query_terms)
        return overlap / len(text_terms)


_VECTOR_STORES: dict[str, ParentChildVectorStore] = {}


def reset_vector_store_registry() -> None:
    """Testing helper to clear in-memory registry."""

    _VECTOR_STORES.clear()


def ingest_documents(
    documents: Iterable[Mapping[str, Any] | SourceDocument],
    *,
    chunk_size: int = 400,
    chunk_overlap: int = 40,
) -> str:
    """Create parent-child chunks and register them in an in-memory store.

    This function mimics a Docling/PyPDFLoader ingest pipeline:
    - uses provided section structure
    - generates parent (section) and child (chunk) pairs
    - attaches metadata (year/citations/authors)
    - registers results and returns a vector_store_uri handle
    """

    normalized = [_normalize_document(doc) for doc in documents]
    vector_store_uri = f"memory://ingest-{uuid.uuid4()}"
    store = ParentChildVectorStore(vector_store_uri)

    for doc in normalized:
        sections = doc.sections or [SourceSection(heading="Full Document", content="")]
        for section in sections:
            if not section.content:
                continue
            parent_id = f"parent-{uuid.uuid4()}"
            parent_metadata = {
                "id": parent_id,
                "type": "parent",
                "title": doc.title,
                "section_heading": section.heading,
                "year": doc.year,
                "citations": doc.citations,
                "authors": doc.authors,
            }
            parent_chunk = Chunk(page_content=section.content, metadata=parent_metadata)

            child_chunks = []
            for index, content in enumerate(
                _split_text(section.content, chunk_size, chunk_overlap)
            ):
                metadata = {
                    "parent_id": parent_id,
                    "section_heading": section.heading,
                    "title": doc.title,
                    "year": doc.year,
                    "citations": doc.citations,
                    "authors": doc.authors,
                    "chunk_index": index,
                }
                child_chunks.append(Chunk(page_content=content, metadata=metadata))

            store.add_section(parent_chunk, child_chunks)

    _VECTOR_STORES[vector_store_uri] = store
    return vector_store_uri


def search_sections(
    query: str,
    *,
    vector_store_uri: str,
    filters: Mapping[str, Any] | None = None,
    k: int = 5,
) -> list[SearchResult]:
    """Search child chunks with optional metadata filtering."""

    if vector_store_uri not in _VECTOR_STORES:
        raise ValueError(f"Unknown vector_store_uri: {vector_store_uri}")
    store = _VECTOR_STORES[vector_store_uri]
    return store.search(query, filters=filters, k=k)


def _normalize_document(doc: Mapping[str, Any] | SourceDocument) -> SourceDocument:
    if isinstance(doc, SourceDocument):
        return doc

    sections_data = doc.get("sections", [])
    sections = [
        SourceSection(heading=section["heading"], content=section["content"])
        for section in sections_data
    ]

    content_fallback = doc.get("content")
    if content_fallback and not sections:
        sections = [SourceSection(heading="Full Document", content=content_fallback)]

    return SourceDocument(
        title=doc.get("title", "Untitled"),
        year=doc.get("year"),
        citations=doc.get("citations"),
        authors=list(doc.get("authors", [])),
        sections=sections,
    )


def _split_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    words = text.split()
    if not words:
        return []

    chunks: list[list[str]] = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunks.append(words[start:end])
        start = end - chunk_overlap
        if start <= 0:
            start = end
    return [" ".join(chunk) for chunk in chunks if chunk]


def _passes_filters(
    metadata: Mapping[str, Any], filters: Mapping[str, Any] | None
) -> bool:
    if not filters:
        return True

    for key, condition in filters.items():
        value = metadata.get(key)
        if isinstance(condition, Mapping):
            for op, expected in condition.items():
                if value is None:
                    return False
                if op == "gte" and not value >= expected:
                    return False
                if op == "lte" and not value <= expected:
                    return False
                if op == "gt" and not value > expected:
                    return False
                if op == "lt" and not value < expected:
                    return False
                if op == "eq" and not value == expected:
                    return False
        else:
            if value != condition:
                return False
    return True


__all__ = [
    "Chunk",
    "ParentChildVectorStore",
    "SearchResult",
    "SourceDocument",
    "SourceSection",
    "ingest_documents",
    "search_sections",
    "reset_vector_store_registry",
]
