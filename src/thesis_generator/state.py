from __future__ import annotations

import operator
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field


class Reference(BaseModel):
    """Metadata for a literature reference used across the workflow."""

    paper_id: str | None = None
    doi: str | None = None
    title: str | None = None
    year: int | None = None
    authors: list[str] = Field(default_factory=list)
    url: str | None = None


class Section(BaseModel):
    """Individual section definition shared by outline/manuscript."""

    id: str
    title: str
    content: str | None = None
    summary: str | None = None
    citations: list[str] = Field(default_factory=list)
    status: Literal["pending", "draft", "in_review", "approved", "rejected"] = "pending"
    feedback: str | None = None


ChapterSummaries = Annotated[dict[str, str], operator.or_]


class ThesisState(BaseModel):
    """Global state shared between LangGraph nodes."""

    topic: str
    target_word_count: int
    style_guide: str

    thesis_title: str | None = None
    hypothesis: str | None = None

    knowledge_graph: list[Reference] = Field(default_factory=list)
    perspectives: list[str] = Field(default_factory=list)

    outline: list[Section] = Field(default_factory=list)
    manuscript: list[Section] = Field(default_factory=list)
    current_section_index: int = 0

    chapter_summaries: ChapterSummaries = Field(default_factory=dict)
    vector_store_uri: str | None = None

    novelty_score: float | None = None
    hallucination_flags: list[str] = Field(default_factory=list)

    user_approval_status: Literal["pending", "approved", "rejected"] = "pending"
    execution_trace: list[str] = Field(default_factory=list)
    next_node: str | None = None

    model_config = ConfigDict(extra="forbid")


class ThesisStateUpdate(BaseModel):
    """Partial update payload for state reducers."""

    topic: str | None = None
    target_word_count: int | None = None
    style_guide: str | None = None
    thesis_title: str | None = None
    hypothesis: str | None = None

    knowledge_graph: list[Reference] | None = None
    perspectives: list[str] | None = None

    outline: list[Section] | None = None
    manuscript: list[Section] | None = None
    current_section_index: int | None = None

    chapter_summaries: ChapterSummaries | None = None
    vector_store_uri: str | None = None

    novelty_score: float | None = None
    hallucination_flags: list[str] | None = None

    user_approval_status: Literal["pending", "approved", "rejected"] | None = None
    execution_trace: list[str] | None = None
    next_node: str | None = None

    model_config = ConfigDict(extra="forbid")


_AGGREGATORS = {"chapter_summaries": operator.or_}


def reduce_state(state: ThesisState, update: ThesisStateUpdate) -> ThesisState:
    """Merge an update into the current state, respecting aggregator semantics."""

    merged = state.model_dump()
    for key, value in update.model_dump(exclude_unset=True).items():
        if key in _AGGREGATORS:
            merged[key] = _AGGREGATORS[key](merged.get(key, {}), value)
        else:
            merged[key] = value

    return ThesisState(**merged)
