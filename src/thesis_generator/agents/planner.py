from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from pydantic import BaseModel, Field

from thesis_generator.state import Section, ThesisState


class FacetProfile(BaseModel):
    """Structured representation of a hypothesis across four facets."""

    purpose: str
    mechanism: str
    evaluation: str
    application: str


class TOCNode(BaseModel):
    """Three-level table of contents node."""

    title: str
    children: list["TOCNode"] = Field(default_factory=list)


@dataclass
class NoveltyResult:
    novelty_score: float
    pivot_required: bool
    overlapping_facet: str | None = None
    closest_similarity: float | None = None


def plan_master_thesis(
    state: ThesisState,
    *,
    facets: FacetProfile | None = None,
    related_profiles: Sequence[FacetProfile] | None = None,
    pivot_threshold: float = 0.75,
) -> ThesisState:
    """Generate a master plan and novelty assessment, updating the ThesisState."""

    base_facets = facets or _default_facets_from_topic(state.topic)
    related = list(related_profiles or [])

    novelty = _assess_novelty(base_facets, related, pivot_threshold=pivot_threshold)
    pivoted = novelty.pivot_required
    final_facets = base_facets
    if pivoted:
        final_facets = _propose_pivot(base_facets, novelty.overlapping_facet)

    hypothesis = _compose_hypothesis(final_facets, pivoted=pivoted)
    toc = _generate_three_level_toc(state.topic, final_facets)
    outline = _flatten_toc(toc)

    return state.model_copy(
        update={
            "hypothesis": hypothesis,
            "outline": outline,
            "novelty_score": round(max(novelty.novelty_score, 0.0), 3),
        }
    )


def _assess_novelty(
    base: FacetProfile,
    related: Sequence[FacetProfile],
    *,
    pivot_threshold: float,
) -> NoveltyResult:
    if not related:
        return NoveltyResult(novelty_score=1.0, pivot_required=False)

    scored: list[tuple[float, str]] = []
    for candidate in related:
        similarity, dominant = _profile_similarity(base, candidate)
        scored.append((similarity, dominant))

    best_similarity, best_facet = max(scored, key=lambda pair: pair[0])
    novelty_score = 1 - best_similarity
    return NoveltyResult(
        novelty_score=novelty_score,
        pivot_required=best_similarity >= pivot_threshold,
        overlapping_facet=best_facet,
        closest_similarity=best_similarity,
    )


def _profile_similarity(base: FacetProfile, candidate: FacetProfile) -> tuple[float, str]:
    facet_scores: dict[str, float] = {}
    for field in ("purpose", "mechanism", "evaluation", "application"):
        facet_scores[field] = _facet_similarity(getattr(base, field), getattr(candidate, field))

    dominant_facet = max(facet_scores.items(), key=lambda pair: pair[1])[0]
    average_similarity = sum(facet_scores.values()) / len(facet_scores)
    return average_similarity, dominant_facet


def _facet_similarity(text_a: str, text_b: str) -> float:
    tokens_a = _tokenize(text_a)
    tokens_b = _tokenize(text_b)
    if not tokens_a or not tokens_b:
        return 0.0

    intersection = tokens_a & tokens_b
    union = tokens_a | tokens_b
    return len(intersection) / len(union) if union else 0.0


def _tokenize(text: str) -> set[str]:
    cleaned = text.replace("/", " ").replace(",", " ")
    return {token.lower() for token in cleaned.split() if token}


def _propose_pivot(base: FacetProfile, overlapping_facet: str | None) -> FacetProfile:
    pivot_hint = {
        "purpose": "human-in-the-loop oversight",
        "mechanism": "retrieval-aware curriculum",
        "evaluation": "longitudinal peer review",
        "application": "low-resource domains",
    }.get(overlapping_facet or "application")

    return base.model_copy(
        update={
            "application": f"{base.application} pivoted toward {pivot_hint}",
            "purpose": base.purpose + " (reframed for novelty)",
        }
    )


def _compose_hypothesis(facets: FacetProfile, *, pivoted: bool) -> str:
    base = (
        f"We hypothesize that {facets.purpose} can be achieved using {facets.mechanism}. "
        f"We will evaluate success via {facets.evaluation} and ground the work in {facets.application}."
    )
    return f"Pivot: {base}" if pivoted else base


def _generate_three_level_toc(topic: str, facets: FacetProfile) -> list[TOCNode]:
    return [
        TOCNode(
            title="Introduction",
            children=[
                TOCNode(
                    title="Motivation and Scope",
                    children=[TOCNode(title=f"Problem framing: {topic}")],
                ),
                TOCNode(
                    title="Central Hypothesis",
                    children=[TOCNode(title=facets.purpose)],
                ),
            ],
        ),
        TOCNode(
            title="Literature Review",
            children=[
                TOCNode(
                    title="STORM Perspectives",
                    children=[TOCNode(title=f"Mechanism landscape: {facets.mechanism}")],
                ),
                TOCNode(
                    title="Novelty Gaps",
                    children=[TOCNode(title=f"Applications frontier: {facets.application}")],
                ),
            ],
        ),
        TOCNode(
            title="Methodology",
            children=[
                TOCNode(
                    title="Planning Graph Design",
                    children=[TOCNode(title="Three-level outline construction")],
                ),
                TOCNode(
                    title="Novelty Evaluation Pipeline",
                    children=[TOCNode(title=f"Metrics: {facets.evaluation}")],
                ),
            ],
        ),
        TOCNode(
            title="Results",
            children=[
                TOCNode(
                    title="Ablation and Baselines",
                    children=[TOCNode(title="Impact of STORM perspectives")],
                ),
                TOCNode(
                    title="Novelty Outcomes",
                    children=[TOCNode(title="Pivot vs non-pivot comparisons")],
                ),
            ],
        ),
        TOCNode(
            title="Discussion",
            children=[
                TOCNode(
                    title="Implications",
                    children=[TOCNode(title="Risks and limitations")],
                ),
                TOCNode(
                    title="Future Work",
                    children=[TOCNode(title="Extending to additional domains")],
                ),
            ],
        ),
        TOCNode(
            title="Conclusion",
            children=[
                TOCNode(
                    title="Summary of Findings",
                    children=[TOCNode(title="Restating the hypothesis and novelty")],
                ),
                TOCNode(
                    title="Practical Recommendations",
                    children=[TOCNode(title="Deployment considerations")],
                ),
            ],
        ),
    ]


def _flatten_toc(nodes: Sequence[TOCNode], prefix: str = "") -> list[Section]:
    sections: list[Section] = []
    for idx, node in enumerate(nodes, start=1):
        number = f"{prefix}{idx}" if prefix else str(idx)
        title = f"{number}. {node.title}"
        sections.append(
            Section(
                id=number,
                title=title,
                content=None,
                summary=None,
                citations=[],
                status="pending",
                feedback=None,
            )
        )
        if node.children:
            sections.extend(_flatten_toc(node.children, prefix=f"{number}."))
    return sections


def _default_facets_from_topic(topic: str) -> FacetProfile:
    return FacetProfile(
        purpose=f"establish a novel thesis plan around {topic}",
        mechanism="storm-style multi-perspective planner",
        evaluation="outline coverage and novelty scoring",
        application="graduate-level research reports",
    )


__all__ = [
    "FacetProfile",
    "NoveltyResult",
    "TOCNode",
    "plan_master_thesis",
]
