from __future__ import annotations

import pytest

from thesis_generator.quality import (
    assign_sources_to_sections,
    calculate_citation_coverage,
    evaluate_quality_gates,
    evaluate_regression_metrics,
    record_slo_metrics,
)
from thesis_generator.state import ResearchDocument, Section, ThesisState


def test_assigns_sources_and_reports_full_coverage() -> None:
    outline = [Section(id="1", title="Intro"), Section(id="2", title="Method")]
    documents = [
        ResearchDocument(id="doc-1", title="One", perspective="tech"),
        ResearchDocument(id="doc-2", title="Two", perspective="policy"),
    ]

    assigned = assign_sources_to_sections(outline, documents, max_sources_per_section=1)
    populated = [
        section.model_copy(update={"citations": list(section.assigned_sources)})
        for section in assigned
    ]

    coverage = calculate_citation_coverage(populated)

    assert all(section.assigned_sources for section in assigned)
    assert coverage.coverage_rate == pytest.approx(1.0)
    assert coverage.missing == {}


def test_quality_gate_warns_on_high_novelty_and_scite_retry() -> None:
    manuscript = [
        Section(
            id="1",
            title="Intro",
            citations=["doc-1"],
            assigned_sources=["doc-1"],
            status="draft",
        )
    ]
    state = ThesisState(
        topic="AI safety",
        target_word_count=1500,
        style_guide="apa",
        manuscript=manuscript,
        novelty_score=0.65,
    )

    report = evaluate_quality_gates(state, scite_failures=1)

    assert report.status == "warn"
    assert report.retry_required is True
    assert any("novelty" in message.lower() for message in report.warnings)


def test_quality_gate_blocks_on_missing_citations_and_false_negatives() -> None:
    manuscript = [
        Section(
            id="1",
            title="Intro",
            citations=["doc-1"],
            assigned_sources=["doc-1", "doc-2"],
            status="draft",
        )
    ]
    state = ThesisState(
        topic="Edge AI",
        target_word_count=2000,
        style_guide="ieee",
        manuscript=manuscript,
        novelty_score=0.2,
    )

    report = evaluate_quality_gates(state, scite_false_negatives=1)

    assert report.status == "block"
    assert any("coverage" in message.lower() for message in report.blocks)
    assert any("false negative" in message.lower() for message in report.blocks)


def test_regression_metrics_flag_failure_on_low_precision() -> None:
    predicted = {"sec-1": {"a", "b"}, "sec-2": {"b"}}
    golden = {"sec-1": {"a"}, "sec-2": {"c"}}

    report = evaluate_regression_metrics(predicted, golden, threshold=0.8)

    assert report.passed is False
    assert report.precision < 1.0
    assert "golden" in report.details.lower()


def test_record_slo_metrics_produces_basic_counters() -> None:
    metrics = record_slo_metrics(
        chapter_durations={"1": 1.2, "2": 2.5},
        vector_search_latencies=[0.1, 0.2],
        scite_success_rate=0.9,
        api_costs={"openai": 1.23},
    )

    assert metrics.avg_chapter_duration == pytest.approx(1.85)
    assert metrics.vector_search_p95 >= metrics.vector_search_p50
    assert metrics.scite_success_rate == 0.9
