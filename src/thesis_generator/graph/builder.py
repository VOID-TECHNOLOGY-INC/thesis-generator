from __future__ import annotations

from collections.abc import Callable
from typing import Any

from langgraph.checkpoint.memory import MemorySaver
from langgraph.constants import END, START
from langgraph.graph import StateGraph

from thesis_generator.agents.researcher import run_researcher_iteration
from thesis_generator.agents.validator import validate_documents
from thesis_generator.agents.writer import draft_manuscript
from thesis_generator.graph.supervisor import RouteResponse, route_next
from thesis_generator.state import ResearchDocument, Section, ThesisState


def _coerce_state(state: ThesisState | dict[str, Any]) -> ThesisState:
    return state if isinstance(state, ThesisState) else ThesisState(**state)


def _supervisor_node(state: ThesisState) -> ThesisState:
    decision: RouteResponse = route_next(state)
    return state.model_copy(update={"next_node": decision.next_agent})


def _researcher_node(state: ThesisState) -> ThesisState:
    updated = run_researcher_iteration(state)
    if not updated.documents:
        seed = ResearchDocument(id="seed-1", title="Placeholder", perspective="general")
        updated = updated.model_copy(update={"documents": updated.documents + [seed]})
    return updated


def _writer_node(state: ThesisState) -> ThesisState:
    current = state
    if not state.outline:
        placeholder_section = Section(id="1", title="Auto-generated section")
        placeholder_doc = ResearchDocument(id="seed-1", title="Placeholder", perspective="general")
        current = state.model_copy(
            update={
                "outline": [placeholder_section],
                "documents": state.documents or [placeholder_doc],
            }
        )
    return draft_manuscript(current)


def _validator_node(state: ThesisState) -> ThesisState:
    validated = validate_documents(state)
    updated_sections = [
        section.model_copy(update={"status": "approved"}) for section in validated.manuscript
    ] if validated.manuscript else validated.manuscript

    return validated.model_copy(
        update={
            "user_approval_status": (
                "approved" if validated.manuscript else validated.user_approval_status
            ),
            "manuscript": updated_sections,
        }
    )


def _analyst_node(state: ThesisState) -> ThesisState:
    # No-op placeholder for synthesis or summarization
    return state


def _routing_key(state: ThesisState | dict[str, Any]) -> str:
    current = _coerce_state(state)
    return route_next(current).next_agent


def build_main_graph(
    *,
    checkpointer: Any | None = None,
    researcher_node: Callable[[ThesisState], ThesisState] = _researcher_node,
    writer_node: Callable[[ThesisState], ThesisState] = _writer_node,
    validator_node: Callable[[ThesisState], ThesisState] = _validator_node,
    analyst_node: Callable[[ThesisState], ThesisState] = _analyst_node,
) -> Any:
    """Construct the main StateGraph for the thesis workflow."""

    workflow = StateGraph(ThesisState)
    workflow.add_node("supervisor", _supervisor_node)
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("writer", writer_node)
    workflow.add_node("validator", validator_node)
    workflow.add_node("analyst", analyst_node)

    workflow.add_edge(START, "supervisor")
    workflow.add_conditional_edges(
        "supervisor",
        _routing_key,
        {
            "researcher": "researcher",
            "writer": "writer",
            "validator": "validator",
            "analyst": "analyst",
            "FINISH": END,
        },
    )

    for node in ("researcher", "writer", "validator", "analyst"):
        workflow.add_edge(node, "supervisor")

    compiled = workflow.compile(checkpointer=checkpointer or MemorySaver())
    return compiled.with_config({"configurable": {"thread_id": "local-thread"}})


__all__ = ["build_main_graph"]
