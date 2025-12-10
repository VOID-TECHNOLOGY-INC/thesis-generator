from thesis_generator.agents.researcher import ResearchDocument
from thesis_generator.agents.validator import validate_documents
from thesis_generator.state import ThesisState


def test_validator_flags_suspicious_sources_with_low_trust() -> None:
    docs = [
        ResearchDocument(
            id="good",
            title="Trustworthy",
            perspective="technical",
            doi="10.good",
            trust_score=None,
        ),
        ResearchDocument(
            id="bad",
            title="Dubious",
            perspective="technical",
            doi="10.bad",
            trust_score=None,
        ),
    ]

    state = ThesisState(topic="AI safety", target_word_count=5000, style_guide="apa", documents=docs)

    def score_fn(dois: list[str]):
        lookup = {
            "10.good": {
                "doi": "10.good",
                "supporting": 10,
                "mentioning": 2,
                "contrasting": 1,
                "trust_score": 0.86,
                "manual_review_required": False,
                "warning": None,
            },
            "10.bad": {
                "doi": "10.bad",
                "supporting": 0,
                "mentioning": 1,
                "contrasting": 4,
                "trust_score": 0.1,
                "manual_review_required": True,
                "warning": "contrasting evidence exceeds supporting",
            },
        }
        return [lookup[doi] for doi in dois]

    updated = validate_documents(state, score_fn=score_fn, min_trust_score=0.5, contrast_ratio=0.6)

    trusted = next(doc for doc in updated.documents if doc.id == "good")
    flagged = next(doc for doc in updated.documents if doc.id == "bad")

    assert trusted.status == "validated"
    assert flagged.status == "excluded"
    assert any("contrasting" in flag for flag in flagged.flags)
    assert flagged.trust_score == 0.1


def test_validator_marks_coverage_gaps_for_manual_review() -> None:
    docs = [
        ResearchDocument(
            id="missing",
            title="No DOI example",
            perspective="policy",
            doi=None,
        )
    ]
    state = ThesisState(topic="OpenAI policy", target_word_count=3000, style_guide="apa", documents=docs)

    updated = validate_documents(state, score_fn=lambda dois: [])

    reviewed = updated.documents[0]
    assert reviewed.status == "needs_review"
    assert any("missing" in flag for flag in reviewed.flags)
