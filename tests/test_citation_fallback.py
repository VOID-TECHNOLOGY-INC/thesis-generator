from __future__ import annotations

from collections.abc import Iterable

import pytest

from thesis_generator.tools.citation_check import evaluate_citations_with_fallback


def test_llm_fallback_scores_when_scite_missing() -> None:
    def fake_fetch(_: str) -> list[str]:
        return ["This study strongly supports the claim", "This contradicts prior work"]

    def fake_classify(contexts: Iterable[str]) -> list[str]:
        labels: list[str] = []
        for text in contexts:
            lower = text.lower()
            if "contradicts" in lower:
                labels.append("contrasting")
            else:
                labels.append("supporting")
        return labels

    results = evaluate_citations_with_fallback(
        ["10.1000/fallback"],
        scite_api_key=None,
        fetch_contexts=fake_fetch,
        classify_fn=fake_classify,
    )

    report = results[0]
    assert report["source"] == "llm_fallback"
    assert report["supporting"] == 1
    assert report["contrasting"] == 1
    assert report["mentioning"] == 0
    assert report["trust_score"] == pytest.approx(0.5, rel=1e-3)
    assert report["manual_review_required"] is False


def test_llm_fallback_warns_when_no_contexts() -> None:
    results = evaluate_citations_with_fallback(
        ["10.1000/empty"],
        fetch_contexts=lambda _: [],
        classify_fn=lambda _: [],
    )

    report = results[0]
    assert report["manual_review_required"] is True
    assert "No citation contexts" in (report.get("warning") or "")
    assert report["trust_score"] == 0.0


def test_llm_fallback_handles_fetch_errors() -> None:
    def fail_fetch(_: str) -> list[str]:
        raise RuntimeError("OpenAlex down")

    results = evaluate_citations_with_fallback(
        ["10.1000/error"],
        fetch_contexts=fail_fetch,
    )

    report = results[0]
    assert report["source"] == "llm_fallback"
    assert report["manual_review_required"] is True
    assert "OpenAlex down" in (report.get("warning") or "")
