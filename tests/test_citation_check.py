from __future__ import annotations

from typing import Any

import pytest

from thesis_generator.tools.citation_check import SciteClient, check_citations


class FakeResponse:
    def __init__(self, status_code: int, payload: dict[str, Any]) -> None:
        self.status_code = status_code
        self._payload = payload

    def raise_for_status(self) -> None:
        if 400 <= self.status_code:
            from requests import HTTPError

            raise HTTPError(response=self)

    def json(self) -> dict[str, Any]:
        return self._payload


class FakeSession:
    def __init__(self, responses: list[FakeResponse]) -> None:
        self.responses = responses
        self.calls: list[tuple[str, dict[str, str] | None]] = []

    def get(self, url: str, *, headers: dict[str, str] | None = None, timeout: int | None = None):
        del timeout  # unused
        if not self.responses:
            raise RuntimeError("No more responses configured")
        self.calls.append((url, headers))
        return self.responses.pop(0)


@pytest.mark.parametrize(
    ("doi", "tallies", "expected_score", "expected_warning"),
    [
        ("10.1000/positive", {"supporting": 4, "mentioning": 2, "contrasting": 1}, 0.714, None),
        ("10.1000/low-evidence", {"supporting": 0, "mentioning": 0, "contrasting": 0}, 0.0, "coverage"),
        ("10.1000/contradict", {"supporting": 1, "mentioning": 0, "contrasting": 3}, 0.25, "contrasting"),
    ],
)
def test_check_citations_scores_and_warnings(
    doi: str, tallies: dict[str, int], expected_score: float, expected_warning: str | None
) -> None:
    response = FakeResponse(200, {"tallies": tallies})
    session = FakeSession([response])
    client = SciteClient(api_key="dummy", session=session)

    report = client.evaluate_doi(doi)

    assert report["doi"] == doi
    assert report["supporting"] == tallies["supporting"]
    assert report["mentioning"] == tallies["mentioning"]
    assert report["contrasting"] == tallies["contrasting"]
    assert report["trust_score"] == pytest.approx(expected_score, rel=1e-3)
    if expected_warning:
        assert expected_warning in (report.get("warning") or "")
    else:
        assert report.get("warning") is None


def test_fallback_on_rate_limit() -> None:
    response = FakeResponse(429, {"message": "rate limit"})
    session = FakeSession([response])
    client = SciteClient(api_key="dummy", session=session)

    report = client.evaluate_doi("10.1000/rate-limit")

    assert report["source"] == "fallback"
    assert report["manual_review_required"] is True
    assert "rate limit" in report["warning"]


def test_fallback_on_unknown_doi() -> None:
    response = FakeResponse(404, {"message": "not found"})
    session = FakeSession([response])
    client = SciteClient(api_key="dummy", session=session)

    report = client.evaluate_doi("10.1000/unknown")

    assert report["source"] == "fallback"
    assert report["manual_review_required"] is True
    assert "coverage" in report["warning"]


def test_check_citations_handles_multiple_dois(monkeypatch: pytest.MonkeyPatch) -> None:
    responses = [
        FakeResponse(200, {"tallies": {"supporting": 2, "mentioning": 1, "contrasting": 0}}),
        FakeResponse(404, {"message": "missing"}),
    ]
    session = FakeSession(responses)
    monkeypatch.setenv("SCITE_API_KEY", "token")

    results = check_citations(["10.1/a", "10.1/missing"], session=session)

    assert len(results) == 2
    assert results[0]["doi"] == "10.1/a"
    assert results[0]["trust_score"] > 0
    assert results[1]["manual_review_required"] is True
    assert results[1]["warning"]
