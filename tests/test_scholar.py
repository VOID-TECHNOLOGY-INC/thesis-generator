from __future__ import annotations

from typing import Any

import pytest

from thesis_generator.tools.scholar import Paper, SemanticScholarAPI


class FakeResponse:
    def __init__(self, status_code: int, payload: dict[str, Any]) -> None:
        self.status_code = status_code
        self._payload = payload

    def json(self) -> dict[str, Any]:
        return self._payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


def test_search_papers_paginates_and_limits_results(monkeypatch: pytest.MonkeyPatch) -> None:
    api = SemanticScholarAPI(api_key="test-key")

    calls: list[dict[str, Any]] = []
    responses = [
        {
            "data": [
                {
                    "paperId": "paper-1",
                    "title": "Graph RAG",
                    "year": 2024,
                    "authors": [{"name": "Ada"}],
                    "citationCount": 10,
                    "influentialCitationCount": 2,
                },
                {
                    "paperId": "paper-2",
                    "title": "Agent RAG",
                    "year": 2023,
                    "authors": [{"name": "Bob"}],
                    "citationCount": 4,
                    "influentialCitationCount": 1,
                },
            ],
            "next": 2,
            "total": 3,
        },
        {
            "data": [
                {
                    "paperId": "paper-3",
                    "title": "Retriever Evaluation",
                    "year": 2022,
                    "authors": [{"name": "Carol"}],
                    "citationCount": 7,
                    "influentialCitationCount": 0,
                }
            ],
            "total": 3,
        },
    ]

    def fake_request(
        method: str, path: str, *, params: dict[str, Any]
    ) -> dict[str, Any]:
        calls.append(params)
        return responses.pop(0)

    monkeypatch.setattr(api, "_request", fake_request)

    papers = api.search_papers("rag", limit=3, per_page=2)

    assert [p.paper_id for p in papers] == ["paper-1", "paper-2", "paper-3"]
    assert calls[0]["offset"] == 0
    assert calls[0]["limit"] == 2
    assert calls[1]["offset"] == 2


def test_request_retries_on_rate_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    api = SemanticScholarAPI(api_key="test-key", max_retries=3, backoff_factor=0)
    responses = [
        FakeResponse(429, {"message": "rate limit"}),
        FakeResponse(200, {"data": []}),
    ]

    def fake_sleep(_: float) -> None:
        return None

    def fake_http_request(
        method: str, url: str, params: dict[str, Any], headers: dict[str, str], timeout: float
    ) -> FakeResponse:
        return responses.pop(0)

    monkeypatch.setattr(api.session, "request", fake_http_request)
    monkeypatch.setattr("time.sleep", fake_sleep)

    payload = api._request("GET", "paper/search", params={"query": "test"})

    assert payload == {"data": []}
    assert not responses


def test_get_paper_details_parses_json(monkeypatch: pytest.MonkeyPatch) -> None:
    api = SemanticScholarAPI(api_key="test-key")

    def fake_request(
        method: str, path: str, *, params: dict[str, Any]
    ) -> dict[str, Any]:
        assert path == "paper/paper-123"
        assert "fields" in params
        return {
            "paperId": "paper-123",
            "title": "Semantic Graphs",
            "abstract": "Explores graph-based retrieval.",
            "year": 2021,
            "authors": [{"name": "Dana"}, {"name": "Eve"}],
            "citationCount": 12,
            "influentialCitationCount": 3,
        }

    monkeypatch.setattr(api, "_request", fake_request)

    paper = api.get_paper_details("paper-123")

    assert isinstance(paper, Paper)
    assert paper.title == "Semantic Graphs"
    assert paper.authors == ["Dana", "Eve"]
    assert paper.citation_count == 12
    assert paper.influential_citation_count == 3
