from __future__ import annotations

import time
from typing import Any, Mapping, Sequence

import requests
from langchain_core.tools import tool
from pydantic import BaseModel, ConfigDict, Field

from thesis_generator.config import load_settings


DEFAULT_FIELDS: list[str] = [
    "paperId",
    "title",
    "abstract",
    "authors",
    "year",
    "citationCount",
    "influentialCitationCount",
]


class Paper(BaseModel):
    """Semantic Scholar paper representation."""

    model_config = ConfigDict(extra="ignore")

    paper_id: str = Field(alias="paperId")
    title: str
    abstract: str | None = None
    year: int | None = None
    authors: list[str] = Field(default_factory=list)
    citation_count: int | None = Field(default=None, alias="citationCount")
    influential_citation_count: int | None = Field(
        default=None, alias="influentialCitationCount"
    )


class SemanticScholarAPI:
    """Lightweight wrapper around the Semantic Scholar Graph API."""

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = "https://api.semanticscholar.org/graph/v1",
        session: requests.Session | None = None,
        max_retries: int = 3,
        backoff_factor: float = 0.5,
        timeout: float = 10.0,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.session = session or requests.Session()
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.timeout = timeout

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Send an HTTP request with simple 429 retry logic."""

        url = f"{self.base_url}/{path.lstrip('/')}"
        headers = {"x-api-key": self.api_key}
        last_response: requests.Response | None = None
        for attempt in range(self.max_retries):
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                headers=headers,
                timeout=self.timeout,
            )
            last_response = response
            if response.status_code == 429 and attempt < self.max_retries - 1:
                delay = self.backoff_factor * (2**attempt)
                time.sleep(delay)
                continue

            if response.status_code >= 400:
                response.raise_for_status()
            return response.json()

        if last_response is not None:
            last_response.raise_for_status()
        raise RuntimeError("Semantic Scholar request failed without response")

    def search_papers(
        self,
        query: str,
        *,
        year_range: tuple[int, int] | None = None,
        limit: int = 20,
        per_page: int = 100,
        fields: Sequence[str] | None = None,
    ) -> list[Paper]:
        """Search papers with pagination and optional year range filter."""

        params: dict[str, Any] = {
            "query": query,
            "offset": 0,
            "limit": min(per_page, limit),
            "fields": ",".join(fields or DEFAULT_FIELDS),
        }
        if year_range:
            params["year"] = f"{year_range[0]}-{year_range[1]}"

        papers: list[Paper] = []
        while len(papers) < limit:
            payload = self._request("GET", "paper/search", params=dict(params))
            data = payload.get("data", []) or []
            for item in data:
                papers.append(self._parse_paper(item))
                if len(papers) >= limit:
                    break

            if len(papers) >= limit:
                break

            next_offset = payload.get("next")
            if next_offset is None:
                params["offset"] = params.get("offset", 0) + params["limit"]
            else:
                params["offset"] = next_offset

            if not data:
                break

        return papers

    def get_paper_details(
        self, paper_id: str, *, fields: Sequence[str] | None = None
    ) -> Paper:
        """Fetch a single paper with the requested fields."""

        payload = self._request(
            "GET",
            f"paper/{paper_id}",
            params={"fields": ",".join(fields or DEFAULT_FIELDS)},
        )
        return self._parse_paper(payload)

    @staticmethod
    def _parse_paper(data: Mapping[str, Any]) -> Paper:
        author_names = [author.get("name") for author in data.get("authors", [])]
        filtered_authors = [name for name in author_names if name]
        normalized: dict[str, Any] = {
            "paperId": data.get("paperId") or "",
            "title": data.get("title") or "",
            "abstract": data.get("abstract"),
            "year": data.get("year"),
            "authors": filtered_authors,
            "citationCount": data.get("citationCount"),
            "influentialCitationCount": data.get("influentialCitationCount"),
        }
        return Paper(**normalized)


def _parse_year_range(value: str | None) -> tuple[int, int] | None:
    if not value:
        return None
    parts = value.split("-")
    if len(parts) == 2 and all(part.isdigit() for part in parts):
        return int(parts[0]), int(parts[1])
    return None


@tool("semantic_scholar_search")
def semantic_scholar_search(
    query: str, year_range: str | None = None, limit: int = 5
) -> list[dict[str, Any]]:
    """Search Semantic Scholar for papers matching a query."""

    settings = load_settings()
    api = SemanticScholarAPI(settings.semantic_scholar_api_key)
    parsed_years = _parse_year_range(year_range)
    papers = api.search_papers(query, year_range=parsed_years, limit=limit)
    return [paper.model_dump() for paper in papers]


@tool("semantic_scholar_get_paper")
def semantic_scholar_get_paper(paper_id: str) -> dict[str, Any]:
    """Fetch a single Semantic Scholar paper by ID."""

    settings = load_settings()
    api = SemanticScholarAPI(settings.semantic_scholar_api_key)
    paper = api.get_paper_details(paper_id)
    return paper.model_dump()


__all__ = [
    "Paper",
    "SemanticScholarAPI",
    "semantic_scholar_get_paper",
    "semantic_scholar_search",
]
