from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from thesis_generator.app import create_app
from thesis_generator.main import run_cli
from thesis_generator.state import ResearchDocument, Section, ThesisState


class _DummyGraph:
    """Simple stand-in graph that marks manuscripts as finished."""

    def __init__(self) -> None:
        self.invocations = 0

    def invoke(self, state: ThesisState) -> ThesisState:
        self.invocations += 1
        manuscript = [
            Section(
                id="1",
                title="Intro",
                content=f"Findings for {state.topic}",
                citations=["ref-1"],
                status="approved",
            )
        ]
        documents = state.documents or [
            ResearchDocument(id="ref-1", title="Seed", perspective="overview")
        ]
        return state.model_copy(
            update={
                "manuscript": manuscript,
                "documents": documents,
                "user_approval_status": "approved",
                "next_node": "FINISH",
            }
        )

    async def astream_events(self, state: ThesisState, **_: object):
        yield {"event": "start", "data": state.model_dump()}
        final_state = self.invoke(state)
        yield {"event": "complete", "data": final_state.model_dump()}


def test_cli_generates_nonempty_markdown(tmp_path: Path) -> None:
    output = tmp_path / "report.md"

    final_state = run_cli(
        ["--topic", "Streaming Interfaces", "--output", str(output)],
        graph_factory=lambda: _DummyGraph(),
    )

    assert output.exists()
    content = output.read_text(encoding="utf-8")
    assert "Streaming Interfaces" in content
    assert "Intro" in content
    assert final_state.next_node == "FINISH"


def test_streaming_endpoint_emits_events() -> None:
    graph = _DummyGraph()
    app = create_app(graph_factory=lambda: graph)
    client = TestClient(app)

    with client.stream("POST", "/run", json={"topic": "Realtime"}) as response:
        lines = [
            line.decode() if isinstance(line, bytes) else line for line in response.iter_lines()
        ]

    assert response.status_code == 200
    assert any('"event": "start"' in line for line in lines)
    assert any('"event": "complete"' in line for line in lines)
