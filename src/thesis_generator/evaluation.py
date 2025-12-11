from __future__ import annotations

import time
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any

from thesis_generator.graph.builder import build_main_graph
from thesis_generator.main import _render_markdown
from thesis_generator.state import Section, ThesisState


def _coerce_state(result: ThesisState | dict[str, Any]) -> ThesisState:
    return result if isinstance(result, ThesisState) else ThesisState(**result)


def _ensure_output_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def run_e2e_suite(
    cases: Iterable[dict[str, Any]],
    *,
    output_dir: Path,
    graph_factory: Callable[[], Any] | None = None,
    time_budget_seconds: float = 300.0,
) -> dict[str, Any]:
    """Run a lightweight end-to-end evaluation for given test cases."""

    _ensure_output_dir(output_dir)
    factory = graph_factory or build_main_graph
    results: list[dict[str, Any]] = []
    completed = 0

    for idx, case in enumerate(cases, start=1):
        topic = str(case.get("topic", "Untitled"))
        target_word_count = int(case.get("target_word_count", 1000))
        style_guide = str(case.get("style_guide", "apa"))
        graph = factory()

        initial_state = ThesisState(
            topic=topic,
            target_word_count=target_word_count,
            style_guide=style_guide,
            outline=[Section(id="1", title="Auto")],
        )

        start = time.perf_counter()
        result = graph.invoke(initial_state)
        duration = time.perf_counter() - start
        final_state = _coerce_state(result)

        output_path = output_dir / f"case_{idx}.md"
        output_path.write_text(_render_markdown(final_state), encoding="utf-8")

        success = duration <= time_budget_seconds and (
            bool(final_state.manuscript) or final_state.next_node == "FINISH"
        )
        completed += int(success)

        results.append(
            {
                "topic": topic,
                "duration_seconds": duration,
                "output_path": output_path,
                "success": success,
            }
        )

    summary = {"total": len(results), "completed": completed}
    return {"summary": summary, "results": results}


__all__ = ["run_e2e_suite"]
