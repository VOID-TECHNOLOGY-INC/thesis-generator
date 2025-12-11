from __future__ import annotations

from thesis_generator.graph.supervisor import RouteResponse, route_next
from thesis_generator.state import ResearchDocument, Section, ThesisState


def _base_state() -> ThesisState:
    return ThesisState(topic="LLM safety", target_word_count=3000, style_guide="apa")


def test_supervisor_routes_to_researcher_when_state_is_empty() -> None:
    state = _base_state()

    decision = route_next(state)

    assert isinstance(decision, RouteResponse)
    assert decision.next_agent == "researcher"
    assert "insufficient" in decision.reasoning.lower()


def test_supervisor_prefers_validator_when_draft_exists_without_review() -> None:
    state = _base_state().model_copy(
        update={
            "outline": [Section(id="1", title="Intro")],
            "manuscript": [
                Section(id="1", title="Intro", content="draft", citations=["a"], status="draft")
            ],
            "documents": [ResearchDocument(id="a", title="A", perspective="tech")],
            "hallucination_flags": [],
        }
    )

    decision = route_next(state)

    assert decision.next_agent == "validator"
    assert "draft" in decision.reasoning.lower()


def test_supervisor_finishes_when_approved_and_clean() -> None:
    manuscript = [
        Section(
            id="1",
            title="Intro",
            content="approved text",
            citations=["a"],
            status="approved",
        )
    ]
    docs = [
        ResearchDocument(id="a", title="Source", perspective="tech", status="validated"),
    ]
    state = _base_state().model_copy(
        update={
            "manuscript": manuscript,
            "documents": docs,
            "user_approval_status": "approved",
        }
    )

    decision = route_next(state)

    assert decision.next_agent == "FINISH"
    assert "complete" in decision.reasoning.lower()
