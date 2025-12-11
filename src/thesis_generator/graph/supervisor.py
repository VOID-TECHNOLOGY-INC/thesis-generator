from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from thesis_generator.state import ThesisState


class RouteResponse(BaseModel):
    """Structured routing decision for the main supervisor."""

    next_agent: Literal["researcher", "writer", "validator", "analyst", "FINISH"]
    reasoning: str = Field(description="Why this agent was chosen")


def _has_complete_manuscript(state: ThesisState) -> bool:
    return bool(state.manuscript) and all(
        section.status == "approved" for section in state.manuscript
    )


def _needs_research(state: ThesisState) -> bool:
    return not state.outline or not state.documents


def _needs_writing(state: ThesisState) -> bool:
    return bool(state.outline) and not state.manuscript


def _needs_validation(state: ThesisState) -> bool:
    return bool(state.manuscript) and state.user_approval_status != "approved"


def route_next(state: ThesisState) -> RouteResponse:
    """Route to the next agent based on current progress."""

    if state.user_approval_status == "approved" or _has_complete_manuscript(state):
        return RouteResponse(
            next_agent="FINISH",
            reasoning="Draft is complete and approved; finishing execution.",
        )

    if _needs_research(state):
        return RouteResponse(
            next_agent="researcher",
            reasoning="Insufficient evidence collected; dispatching researcher.",
        )

    if _needs_writing(state):
        return RouteResponse(
            next_agent="writer",
            reasoning="Outline exists without a draft; delegating writing.",
        )

    if _needs_validation(state):
        return RouteResponse(
            next_agent="validator",
            reasoning="Draft present but unverified; sending to validator.",
        )

    return RouteResponse(
        next_agent="analyst",
        reasoning="Routing to analyst for summarization or synthesis.",
    )


__all__ = ["RouteResponse", "route_next"]
