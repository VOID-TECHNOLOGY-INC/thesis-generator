from __future__ import annotations

from typing import Any

import pytest

from thesis_generator.tools.openalex import OpenAlexAPI, OpenAlexPaper


class FakeWorks:
    def __init__(
        self,
        pages: list[list[dict[str, Any]]] | None = None,
        details: dict[str, dict[str, Any]] | None = None,
    ) -> None:
        self.pages = pages or []
        self.details = details or {}
        self.params: dict[str, Any] | None = None
        self.per_page: int | None = None

    def search(self, s: str) -> FakeWorks:
        self.params = self.params or {}
        self.params["search"] = s
        return self

    def select(self, s: str) -> FakeWorks:
        self.params = self.params or {}
        self.params["select"] = s
        return self

    def filter(self, **kwargs: Any) -> FakeWorks:
        self.params = self.params or {}
        filters = self.params.get("filter", {})
        filters.update(kwargs)
        self.params["filter"] = filters
        return self

    def paginate(self, per_page: int | None = None, **_: Any):
        self.per_page = per_page
        return iter(self.pages)

    def get(self, per_page: int | None = None, page: int | None = None, cursor: str | None = None):
        del page, cursor  # unused
        self.per_page = per_page
        filters = (self.params or {}).get("filter", {})
        work_id = filters.get("openalex_id")
        if work_id is None:
            return []
        if isinstance(work_id, list):
            return [self.details[i] for i in work_id if i in self.details]
        return [self.details.get(work_id)].copy() if work_id in self.details else []


def test_search_papers_paginates_and_limits_results() -> None:
    pages = [
        [
            {
                "id": "W1",
                "display_name": "Graph RAG",
                "publication_year": 2024,
                "authorships": [{"author": {"display_name": "Ada"}}],
                "cited_by_count": 10,
                "abstract_inverted_index": {"Graph": [0], "RAG": [1]},
            },
            {
                "id": "W2",
                "display_name": "Agent RAG",
                "publication_year": 2023,
                "authorships": [{"author": {"display_name": "Bob"}}],
                "cited_by_count": 4,
                "abstract_inverted_index": {"Agent": [0], "RAG": [1]},
            },
        ],
        [
            {
                "id": "W3",
                "display_name": "Retriever Evaluation",
                "publication_year": 2022,
                "authorships": [{"author": {"display_name": "Carol"}}],
                "cited_by_count": 7,
                "abstract_inverted_index": {"Retriever": [0], "Evaluation": [1]},
            }
        ],
    ]
    works = FakeWorks(pages=pages)
    api = OpenAlexAPI(works_client=works, max_results_per_page=2)

    papers = api.search_papers("rag", year_range=(2020, 2024), limit=3, per_page=2)

    assert [p.paper_id for p in papers] == ["W1", "W2", "W3"]
    assert works.per_page == 2
    assert works.params["filter"]["publication_year"] == "2020-2024"


def test_get_paper_details_parses_json() -> None:
    details = {
        "W123": {
            "id": "W123",
            "display_name": "Semantic Graphs",
            "abstract_inverted_index": {"Semantic": [0], "Graphs": [1]},
            "publication_year": 2021,
            "authorships": [
                {"author": {"display_name": "Dana"}},
                {"author": {"display_name": "Eve"}},
            ],
            "cited_by_count": 12,
            "referenced_works": ["W1", "W2"],
        }
    }
    works = FakeWorks(details=details)
    api = OpenAlexAPI(works_client=works)

    paper = api.get_paper_details("W123")

    assert isinstance(paper, OpenAlexPaper)
    assert paper.title == "Semantic Graphs"
    assert paper.authors == ["Dana", "Eve"]
    assert paper.citation_count == 12
    assert paper.referenced_works == ["W1", "W2"]
    assert paper.abstract is not None


def test_get_paper_details_missing_raises() -> None:
    works = FakeWorks(details={})
    api = OpenAlexAPI(works_client=works)

    with pytest.raises(RuntimeError):
        api.get_paper_details("W999")
