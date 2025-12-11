import pytest

from thesis_generator.agents.researcher import generate_perspectives, run_researcher_iteration
from thesis_generator.state import ThesisState


@pytest.fixture()
def base_state() -> ThesisState:
    return ThesisState(topic="AI safety", target_word_count=5000, style_guide="apa")


def test_generate_perspectives_returns_unique_and_varied() -> None:
    perspectives = generate_perspectives("graph-based recommender systems", min_count=4)

    assert len(perspectives) >= 4
    assert len(set(perspectives)) == len(perspectives)
    assert any("economic" in p.lower() or "policy" in p.lower() for p in perspectives)
    assert any("technical" in p.lower() or "robust" in p.lower() for p in perspectives)


def test_researcher_updates_state_with_perspective_metadata(base_state: ThesisState) -> None:
    perspectives = ["technical risks", "economic impact"]

    def search_fn(topic: str, perspective: str):
        return [
            {
                "paper_id": f"{perspective[:3]}-1",
                "title": f"{perspective.title()} study",
                "abstract": f"Insights about {topic} from {perspective} lens",
                "year": 2024,
                "citation_count": 12,
            }
        ]

    def conversation_fn(perspective: str):
        return [f"How does {perspective} evolve?", f"What are open questions in {perspective}?"]

    updated = run_researcher_iteration(
        base_state,
        perspectives=perspectives,
        search_fn=search_fn,
        conversation_fn=conversation_fn,
        max_results=1,
    )

    assert updated.perspectives == perspectives
    assert len(updated.documents) == len(perspectives)
    assert all(doc.perspective in perspectives for doc in updated.documents)
    assert all(doc.summary and doc.perspective in doc.summary for doc in updated.documents)
    assert all(doc.metadata.get("conversation_questions") for doc in updated.documents)
