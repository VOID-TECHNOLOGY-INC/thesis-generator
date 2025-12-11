from thesis_generator.agents.researcher import ResearchDocument
from thesis_generator.agents.writer import draft_manuscript
from thesis_generator.state import Section, ThesisState


def test_writer_enforces_citation_per_paragraph() -> None:
    outline = [
        Section(id="1", title="1. Introduction"),
        Section(id="2", title="2. Methods"),
    ]
    documents = [
        ResearchDocument(id="D1", title="Paper One", perspective="technical"),
        ResearchDocument(id="D2", title="Paper Two", perspective="policy"),
    ]
    state = ThesisState(
        topic="Robust AI agents",
        target_word_count=4000,
        style_guide="apa",
        outline=outline,
        documents=documents,
    )

    updated = draft_manuscript(state, max_paragraph_length=180)

    assert len(updated.manuscript) == len(outline)
    for section in updated.manuscript:
        paragraphs = section.content.split("\n\n")
        assert section.citations, "each section should collect citations"
        for para in paragraphs:
            assert "[" in para and "]" in para
            assert any(doc.id in para for doc in documents)


def test_writer_splits_long_content_with_revision_loop() -> None:
    outline = [Section(id="1", title="1. Discussion")]
    documents = [
        ResearchDocument(id="D1", title="Long Form Paper", perspective="analysis"),
    ]
    state = ThesisState(
        topic="Autonomous agents",
        target_word_count=2000,
        style_guide="apa",
        outline=outline,
        documents=documents,
    )

    updated = draft_manuscript(state, max_paragraph_length=80)

    lengths = [len(p) for p in updated.manuscript[0].content.split("\n\n")]
    assert all(length <= 100 for length in lengths)
