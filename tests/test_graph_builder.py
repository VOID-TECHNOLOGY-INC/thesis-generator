from __future__ import annotations

from langgraph.constants import END, START

from thesis_generator.graph.builder import build_main_graph
from thesis_generator.state import ResearchDocument, Section, ThesisState


def test_graph_compiles_without_isolated_nodes() -> None:
    app = build_main_graph()
    graph = app.get_graph()

    node_ids = set(graph.nodes.keys())
    edge_pairs = {(edge.source, edge.target) for edge in graph.edges}

    # every node should participate in at least one edge (start/end excepted)
    for node in node_ids:
        if node in {START, END}:
            continue
        assert any(node in pair for pair in edge_pairs), f"{node} is isolated"


def test_graph_runs_from_start_to_finish() -> None:
    app = build_main_graph()
    initial = ThesisState(
        topic="Evaluating RAG systems",
        target_word_count=1000,
        style_guide="apa",
        outline=[Section(id="1", title="Intro")],
        documents=[ResearchDocument(id="d1", title="Doc", perspective="tech", doi="10.0/1")],
    )

    result = app.invoke(initial)

    assert result.get("manuscript"), "writer should populate manuscript"
    assert result.get("documents"), "documents should persist through the graph"
    assert result.get("next_node") == "FINISH"
