from __future__ import annotations

import argparse
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from thesis_generator.graph.builder import build_main_graph
from thesis_generator.state import Section, ThesisState


def _coerce_state(result: ThesisState | Mapping[str, Any]) -> ThesisState:
    return result if isinstance(result, ThesisState) else ThesisState(**result)


def _render_markdown(state: ThesisState) -> str:
    lines: list[str] = [f"# {state.topic}", ""]
    if state.thesis_title:
        lines.insert(1, f"## {state.thesis_title}")
    if not state.manuscript:
        lines.append("_No manuscript generated._")
        return "\n".join(lines)

    for section in state.manuscript:
        heading = f"## {section.title}"
        body = section.content or ""
        citations = ", ".join(section.citations) if section.citations else ""
        footer = f"\n\n_Citations: {citations}_" if citations else ""
        lines.extend([heading, "", body + footer, ""])
    return "\n".join(lines).strip() + "\n"


def run_cli(
    argv: list[str] | None = None,
    *,
    graph_factory: Callable[[], object] | None = None,
) -> ThesisState:
    """Entrypoint for CLI usage; returns the final ThesisState."""

    parser = argparse.ArgumentParser(description="Run the thesis generator workflow.")
    parser.add_argument("--topic", required=True, help="Research topic to explore.")
    parser.add_argument(
        "--target-word-count",
        type=int,
        default=1200,
        help="Desired total word count for the manuscript.",
    )
    parser.add_argument(
        "--style-guide",
        default="apa",
        help="Styling guideline such as apa or ieee.",
    )
    parser.add_argument(
        "--output",
        default="thesis.md",
        help="Path to write the generated markdown.",
    )

    args = parser.parse_args(argv)

    app: Any = graph_factory() if graph_factory else build_main_graph()
    initial_state = ThesisState(
        topic=args.topic,
        target_word_count=args.target_word_count,
        style_guide=args.style_guide,
        outline=[Section(id="1", title="Introduction")],
    )

    result = app.invoke(initial_state)
    final_state = _coerce_state(result)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(_render_markdown(final_state), encoding="utf-8")

    return final_state


__all__ = ["run_cli"]
