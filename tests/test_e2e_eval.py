from __future__ import annotations

from pathlib import Path

from thesis_generator.evaluation import run_e2e_suite
from thesis_generator.state import ThesisState


class _TinyGraph:
    def invoke(self, state: ThesisState) -> ThesisState:
        return state.model_copy(update={"manuscript": state.manuscript or [], "next_node": "FINISH"})


def test_e2e_suite_produces_metrics(tmp_path: Path) -> None:
    cases = [{"topic": "Edge AI", "target_word_count": 400, "style_guide": "apa"}]

    report = run_e2e_suite(
        cases,
        output_dir=tmp_path,
        graph_factory=lambda: _TinyGraph(),
        time_budget_seconds=2.0,
    )

    assert report["summary"]["completed"] == 1
    assert report["results"][0]["duration_seconds"] < 2.0
    assert report["results"][0]["output_path"].exists()
