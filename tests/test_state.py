import pytest
from pydantic import ValidationError

from thesis_generator.state import ThesisState, ThesisStateUpdate, reduce_state


def test_chapter_summaries_reduce_merges_entries() -> None:
    base = ThesisState(
        topic="Autonomous agents for research",
        target_word_count=12000,
        style_guide="APA",
        chapter_summaries={"1": "Introduction summary"},
    )
    update = ThesisStateUpdate(chapter_summaries={"2": "Methods summary"})

    merged = reduce_state(base, update)

    assert merged.chapter_summaries == {
        "1": "Introduction summary",
        "2": "Methods summary",
    }


def test_thesis_state_validates_field_types() -> None:
    with pytest.raises(ValidationError):
        ThesisState(
            topic="RAG pipelines",
            target_word_count=8000,
            style_guide="ACM",
            knowledge_graph="not-a-list",  # type: ignore[arg-type]
        )
