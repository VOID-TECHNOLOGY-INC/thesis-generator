from __future__ import annotations

from collections.abc import Iterable
from itertools import cycle, islice

from thesis_generator.state import ResearchDocument, Section, ThesisState


def _chunk_paragraphs(text: str, citation: str, limit: int) -> list[str]:
    sentences = [part.strip() for part in text.split(".") if part.strip()]
    paragraphs: list[str] = []
    current = ""

    for sentence in sentences:
        candidate = f"{current} {sentence}".strip() if current else sentence
        if len(candidate) + len(citation) + 1 > limit and current:
            paragraphs.append(f"{current.strip()} {citation}".strip())
            current = sentence
        else:
            current = candidate
    if current:
        paragraphs.append(f"{current.strip()} {citation}".strip())
    return paragraphs or [f"{text.strip()} {citation}".strip()]


def _build_paragraph(doc: ResearchDocument, section: Section) -> str:
    base = (
        f"{section.title} integrates findings from {doc.title} "
        f"through the lens of {doc.perspective.lower()}."
    )
    if doc.summary:
        base += f" Key point: {doc.summary}"
    return base


def draft_manuscript(state: ThesisState, *, max_paragraph_length: int = 180) -> ThesisState:
    """Draft sections ensuring each paragraph carries a citation marker."""

    usable_docs = [doc for doc in state.documents if doc.status != "excluded"]
    if not usable_docs:
        usable_docs = list(state.documents) or [
            ResearchDocument(id="ref-1", title="Placeholder", perspective="general")
        ]

    manuscripts: list[Section] = []
    doc_cycle: Iterable[ResearchDocument] = cycle(usable_docs)

    for section in state.outline:
        doc_batch = list(islice(doc_cycle, 2)) or list(usable_docs[:1])
        paragraphs: list[str] = []
        citations: list[str] = []

        for doc in doc_batch:
            citation = f"[{doc.id}]"
            citations.append(doc.id)
            text = _build_paragraph(doc, section)
            paragraphs.extend(_chunk_paragraphs(text, citation, max_paragraph_length))

        content = "\n\n".join(paragraphs)
        manuscripts.append(
            Section(
                id=section.id,
                title=section.title,
                content=content,
                citations=citations,
                status="draft",
            )
        )

    return state.model_copy(update={"manuscript": manuscripts})


__all__ = ["draft_manuscript"]
