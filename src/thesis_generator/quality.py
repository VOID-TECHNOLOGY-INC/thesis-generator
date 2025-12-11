from __future__ import annotations

import math
from collections.abc import Collection, Iterable, Mapping, Sequence
from dataclasses import dataclass, field

from thesis_generator.state import ResearchDocument, Section, ThesisState


@dataclass
class CitationCoverage:
    coverage_rate: float
    missing: dict[str, set[str]]
    total_assigned: int
    total_cited: int


def assign_sources_to_sections(
    outline: Sequence[Section],
    documents: Sequence[ResearchDocument],
    *,
    max_sources_per_section: int = 2,
) -> list[Section]:
    """Assign sources to sections in a round-robin manner."""

    if not outline:
        return []
    if not documents:
        return [section.model_copy() for section in outline]

    assigned: list[Section] = []
    doc_ids = [doc.id for doc in documents]
    idx = 0

    for section in outline:
        count = max(1, max_sources_per_section)
        sources: list[str] = []
        for _ in range(count):
            sources.append(doc_ids[idx % len(doc_ids)])
            idx += 1
        updated = section.model_copy(update={"assigned_sources": sources})
        assigned.append(updated)

    return assigned


def calculate_citation_coverage(sections: Iterable[Section]) -> CitationCoverage:
    """Compute how many assigned sources are actually cited."""

    missing: dict[str, set[str]] = {}
    total_assigned = 0
    total_cited = 0

    for section in sections:
        assigned_set = set(section.assigned_sources or [])
        cited_set = set(section.citations or [])
        total_assigned += len(assigned_set)
        total_cited += len(cited_set)

        diff = assigned_set - cited_set
        if diff:
            missing[section.id] = diff

    coverage_rate = (
        (total_assigned - sum(len(v) for v in missing.values())) / total_assigned
        if total_assigned
        else 1.0
    )

    return CitationCoverage(
        coverage_rate=coverage_rate,
        missing=missing,
        total_assigned=total_assigned,
        total_cited=total_cited,
    )


@dataclass
class QualityGateReport:
    status: str
    warnings: list[str] = field(default_factory=list)
    blocks: list[str] = field(default_factory=list)
    retry_required: bool = False
    coverage: CitationCoverage | None = None
    novelty_score: float | None = None


def evaluate_quality_gates(
    state: ThesisState,
    *,
    scite_failures: int = 0,
    scite_false_positives: int = 0,
    scite_false_negatives: int = 0,
    coverage_warn_threshold: float = 0.98,
    coverage_block_threshold: float = 1.0,
    novelty_warn: float = 0.6,
    novelty_block: float = 0.7,
) -> QualityGateReport:
    """Apply staged quality gates for novelty, citation coverage, and Scite health."""

    warnings: list[str] = []
    blocks: list[str] = []
    coverage = calculate_citation_coverage(state.manuscript)

    if coverage.coverage_rate < coverage_block_threshold and coverage.missing:
        blocks.append("Citation coverage below required 100%; missing citations present.")
    elif coverage.coverage_rate < coverage_warn_threshold:
        warnings.append("Citation coverage below 98%; review missing citations.")

    novelty = state.novelty_score
    if novelty is not None:
        if novelty >= novelty_block:
            blocks.append(f"Novelty score {novelty:.2f} exceeds blocking threshold.")
        elif novelty >= novelty_warn:
            warnings.append(f"Novelty score {novelty:.2f} exceeds warning threshold.")

    if scite_false_positives or scite_false_negatives:
        blocks.append(
            f"Scite validation produced false positives ({scite_false_positives})"
            f" / false negatives ({scite_false_negatives}); manual review required."
        )

    retry_required = False
    if scite_failures > 0:
        warnings.append("Scite failures encountered; retry validation.")
        retry_required = True

    status = "pass"
    if blocks:
        status = "block"
    elif warnings:
        status = "warn"

    return QualityGateReport(
        status=status,
        warnings=warnings,
        blocks=blocks,
        retry_required=retry_required,
        coverage=coverage,
        novelty_score=novelty,
    )


@dataclass
class RegressionReport:
    precision: float
    recall: float
    f1: float
    passed: bool
    details: str


def evaluate_regression_metrics(
    predicted: Mapping[str, Collection[str]],
    golden: Mapping[str, Collection[str]],
    threshold: float = 0.9,
) -> RegressionReport:
    """Evaluate citation precision/recall against a golden set."""

    pred_set = {(sec, ref) for sec, refs in predicted.items() for ref in refs}
    gold_set = {(sec, ref) for sec, refs in golden.items() for ref in refs}

    true_positive = len(pred_set & gold_set)
    total_pred = len(pred_set)
    total_gold = len(gold_set)

    precision = true_positive / total_pred if total_pred else 0.0
    recall = true_positive / total_gold if total_gold else 0.0
    f1 = 0.0 if not (precision + recall) else 2 * precision * recall / (precision + recall)

    passed = precision >= threshold and recall >= threshold
    extra = pred_set - gold_set
    missing = gold_set - pred_set
    details = (
        f"extra: {sorted(extra)} missing: {sorted(missing)}; "
        f"golden size={total_gold}, predicted={total_pred}"
    )

    return RegressionReport(
        precision=precision,
        recall=recall,
        f1=f1,
        passed=passed,
        details=details,
    )


@dataclass
class SLOMetrics:
    avg_chapter_duration: float
    vector_search_p50: float
    vector_search_p95: float
    scite_success_rate: float
    api_costs: dict[str, float]


def _percentile(values: Sequence[float], percentile: float) -> float:
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    k = (len(sorted_vals) - 1) * percentile
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_vals[int(k)]
    d0 = sorted_vals[f] * (c - k)
    d1 = sorted_vals[c] * (k - f)
    return d0 + d1


def record_slo_metrics(
    *,
    chapter_durations: Mapping[str, float],
    vector_search_latencies: Sequence[float],
    scite_success_rate: float,
    api_costs: Mapping[str, float] | None = None,
) -> SLOMetrics:
    """Summarize SLO and cost metrics for monitoring/alerting."""

    durations = list(chapter_durations.values())
    avg_duration = float(sum(durations) / len(durations)) if durations else 0.0
    vector_p50 = _percentile(vector_search_latencies, 0.5)
    vector_p95 = _percentile(vector_search_latencies, 0.95)

    return SLOMetrics(
        avg_chapter_duration=avg_duration,
        vector_search_p50=vector_p50,
        vector_search_p95=vector_p95,
        scite_success_rate=scite_success_rate,
        api_costs=dict(api_costs or {}),
    )


__all__ = [
    "CitationCoverage",
    "QualityGateReport",
    "RegressionReport",
    "SLOMetrics",
    "assign_sources_to_sections",
    "calculate_citation_coverage",
    "evaluate_quality_gates",
    "evaluate_regression_metrics",
    "record_slo_metrics",
]
