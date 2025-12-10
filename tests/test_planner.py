import pytest

from thesis_generator.agents.planner import FacetProfile, plan_master_thesis
from thesis_generator.state import ThesisState


@pytest.fixture()
def base_state() -> ThesisState:
    return ThesisState(
        topic="Graph RAG for scientific discovery",
        target_word_count=6000,
        style_guide="apa",
    )


def test_planner_triggers_pivot_when_profile_matches_existing(base_state: ThesisState) -> None:
    facets = FacetProfile(
        purpose="accelerate literature review",
        mechanism="graph retriever with contrastive reranking",
        evaluation="citation precision on QA benchmarks",
        application="computational biology datasets",
    )

    related = [
        FacetProfile(
            purpose="accelerate literature review",
            mechanism="graph retriever with contrastive reranking",
            evaluation="citation precision on QA benchmarks",
            application="computational biology datasets",
        )
    ]

    updated = plan_master_thesis(
        base_state,
        facets=facets,
        related_profiles=related,
        pivot_threshold=0.8,
    )

    assert updated.novelty_score is not None and updated.novelty_score < 0.3
    assert updated.hypothesis is not None
    assert "pivot" in updated.hypothesis.lower()
    assert updated.hypothesis != base_state.hypothesis
    assert updated.outline, "planner should lock an outline into the state"


def test_planner_generates_three_level_toc_with_core_chapters(base_state: ThesisState) -> None:
    facets = FacetProfile(
        purpose="human-guided thesis planning",
        mechanism="storm-style perspective synthesis",
        evaluation="reviewer alignment and novelty scoring",
        application="autonomous thesis assistants",
    )

    updated = plan_master_thesis(
        base_state,
        facets=facets,
        related_profiles=[],
        pivot_threshold=0.8,
    )

    titles = [section.title for section in updated.outline]
    required = [
        "Introduction",
        "Literature Review",
        "Methodology",
        "Results",
        "Discussion",
        "Conclusion",
    ]

    for chapter in required:
        assert any(chapter.lower() in title.lower() for title in titles)

    assert any(title.count(".") >= 2 for title in titles), "outline should reach 3 levels"
    assert updated.hypothesis is not None
    assert updated.novelty_score is not None
