from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any

from thesis_generator.state import ResearchDocument, ThesisState
from thesis_generator.tools.citation_check import evaluate_citations_with_fallback


def _evaluate(
    dois: list[str],
    score_fn: Callable[[list[str]], Sequence[Mapping[str, Any]]] | None,
) -> dict[str, Mapping[str, Any]]:
    if not dois:
        return {}
    scores = score_fn(dois) if score_fn else evaluate_citations_with_fallback(dois)
    return {str(entry.get("doi")): entry for entry in scores if entry.get("doi")}


def validate_documents(
    state: ThesisState,
    *,
    score_fn: Callable[[list[str]], Sequence[Mapping[str, Any]]] | None = None,
    min_trust_score: float = 0.5,
    contrast_ratio: float = 1.0,
) -> ThesisState:
    """Score research documents and flag suspicious sources."""

    documents: list[ResearchDocument] = []
    doi_map = _evaluate(
        [doc.doi for doc in state.documents if doc.doi],
        score_fn,
    )
    hallucination_flags = list(state.hallucination_flags)

    for doc in state.documents:
        updated = doc.model_copy()
        flags: list[str] = list(doc.flags)

        if not doc.doi:
            updated.status = "needs_review"
            updated.trust_score = 0.0
            flags.append("missing_doi")
        elif doc.doi in doi_map:
            score = doi_map[doc.doi]
            trust = float(score.get("trust_score") or 0.0)
            updated.trust_score = trust
            warning = str(score.get("warning") or "")
            supporting = int(score.get("supporting") or 0)
            contrasting = int(score.get("contrasting") or 0)
            manual = bool(score.get("manual_review_required"))

            if warning:
                flags.append(warning)
            if manual:
                flags.append("manual_review_required")
            if contrasting > max(1, supporting) * contrast_ratio:
                flags.append("contrasting evidence exceeds supporting")
            if trust < min_trust_score:
                flags.append("trust_score_below_threshold")

            if flags:
                updated.status = "excluded"
                hallucination_flags.append(f"{doc.id}: {'; '.join(flags)}")
            else:
                updated.status = "validated"
        else:
            updated.status = "needs_review"
            updated.trust_score = 0.0
            flags.append("no_scite_coverage")

        updated.flags = sorted(set(flags))
        documents.append(updated)

    return state.model_copy(update={"documents": documents, "hallucination_flags": hallucination_flags})


__all__ = ["validate_documents"]
