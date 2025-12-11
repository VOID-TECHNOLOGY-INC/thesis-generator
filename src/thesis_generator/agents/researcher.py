from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any

from thesis_generator.state import ResearchDocument, ThesisState

_DEFAULT_PERSPECTIVES = [
    "Technical robustness",
    "Economic impact",
    "Policy and governance",
    "Human factors",
    "Historical precedents",
]


def generate_perspectives(topic: str, min_count: int = 3) -> list[str]:
    """Generate diverse, de-duplicated STORM-style perspectives."""

    seeds = [f"{item} of {topic}".strip() for item in _DEFAULT_PERSPECTIVES]
    unique: list[str] = []
    seen: set[str] = set()
    for candidate in seeds:
        key = candidate.lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(candidate)
        if len(unique) >= min_count:
            break
    while len(unique) < max(min_count, 3):
        extra = f"Exploratory angle {len(unique)+1} on {topic}"
        if extra.lower() not in seen:
            unique.append(extra)
            seen.add(extra.lower())
    return unique


def _summarize_abstract(abstract: str | None, perspective: str) -> str:
    snippet = (abstract or "").strip()
    if snippet:
        snippet = snippet.split("\n")[0]
        snippet = snippet[:180]
    else:
        snippet = "summary pending"
    return f"{perspective}: {snippet}"


def run_researcher_iteration(
    state: ThesisState,
    *,
    perspectives: Sequence[str] | None = None,
    search_fn: Callable[[str, str], Sequence[Mapping[str, Any]]] | None = None,
    conversation_fn: Callable[[str], Sequence[str]] | None = None,
    max_results: int = 2,
) -> ThesisState:
    """Execute a lightweight STORM research loop and enrich the state."""

    chosen = list(perspectives or generate_perspectives(state.topic))
    deduped: list[str] = []
    seen: set[str] = set()
    for perspective in chosen:
        normalized = perspective.strip()
        key = normalized.lower()
        if not normalized or key in seen:
            continue
        seen.add(key)
        deduped.append(normalized)

    documents = list(state.documents)
    search = search_fn or (lambda _topic, _perspective: [])

    for perspective in deduped:
        questions = list(conversation_fn(perspective)) if conversation_fn else []
        results = list(search(state.topic, perspective))[: max_results or 1]
        for idx, item in enumerate(results):
            doc = ResearchDocument(
                id=str(item.get("paper_id") or item.get("doi") or f"{perspective[:3]}-{idx}"),
                title=str(item.get("title") or f"{perspective.title()} insight"),
                abstract=item.get("abstract"),
                perspective=perspective,
                summary=_summarize_abstract(item.get("abstract"), perspective),
                doi=item.get("doi"),
                paper_id=item.get("paper_id"),
                year=item.get("year"),
                citation_count=item.get("citation_count"),
                metadata={"conversation_questions": questions},
            )
            documents.append(doc)

    return state.model_copy(update={"perspectives": deduped, "documents": documents})


__all__ = ["generate_perspectives", "run_researcher_iteration"]
