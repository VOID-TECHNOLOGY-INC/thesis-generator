from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from langchain_core.tools import tool
    from pyalex import Works
    from pyalex import config as openalex_config
    from pyalex import invert_abstract
else:
    def tool(*args: Any, **kwargs: Any):
        def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
            return fn

        if args and callable(args[0]) and len(args) == 1 and not kwargs:
            return decorator(args[0])
        return decorator

    class _OpenAlexConfig:
        mailto: str | None = None

    openalex_config = _OpenAlexConfig()
    Works = None

    def invert_abstract(index: Mapping[str, list[int]]) -> str:
        # Basic fallback that reverses the inverted index into text.
        words = sorted(((pos, token) for token, positions in index.items() for pos in positions))
        return " ".join(token for _, token in words)
from pydantic import BaseModel, ConfigDict, Field

from thesis_generator.config import load_settings

DEFAULT_FIELDS: list[str] = [
    "id",
    "display_name",
    "abstract_inverted_index",
    "publication_year",
    "authorships.author.display_name",
    "cited_by_count",
    "referenced_works",
]


class OpenAlexPaper(BaseModel):
    """OpenAlex work representation."""

    model_config = ConfigDict(extra="ignore")

    paper_id: str = Field(alias="paperId")
    title: str
    abstract: str | None = None
    year: int | None = None
    authors: list[str] = Field(default_factory=list)
    citation_count: int | None = Field(default=None, alias="citationCount")
    referenced_works: list[str] = Field(default_factory=list)


class OpenAlexAPI:
    """Lightweight wrapper around the OpenAlex API via pyalex."""

    def __init__(
        self,
        *,
        mailto: str | None = None,
        works_client: Any | None = None,
        max_results_per_page: int = 100,
    ) -> None:
        if mailto and hasattr(openalex_config, "mailto"):
            openalex_config.mailto = mailto
        if works_client is not None:
            self.works = works_client
        elif Works is not None:
            self.works = Works()
        else:  # pragma: no cover - only when pyalex is absent
            raise RuntimeError("pyalex is not installed; provide a works_client.")
        self.max_results_per_page = max(1, min(max_results_per_page, 200))

    def search_papers(
        self,
        query: str,
        *,
        year_range: tuple[int, int] | None = None,
        limit: int = 20,
        per_page: int = 100,
        fields: Sequence[str] | None = None,
    ) -> list[OpenAlexPaper]:
        """Search works with pagination and optional year filter."""

        request = self.works.search(query)
        request = request.select(",".join(fields or DEFAULT_FIELDS))

        if year_range:
            request = request.filter(publication_year=f"{year_range[0]}-{year_range[1]}")

        page_size = max(1, min(per_page, limit, self.max_results_per_page))
        papers: list[OpenAlexPaper] = []

        for page in request.paginate(per_page=page_size):
            if not page:
                break

            for item in page:
                papers.append(self._parse_work(item))
                if len(papers) >= limit:
                    return papers

        return papers

    def get_paper_details(
        self, work_id: str, *, fields: Sequence[str] | None = None
    ) -> OpenAlexPaper:
        """Fetch a single work with the requested fields."""

        request = self.works.filter(openalex_id=work_id).select(
            ",".join(fields or DEFAULT_FIELDS)
        )
        results = request.get(per_page=1)

        if not results:
            raise RuntimeError(f"OpenAlex work not found: {work_id}")

        return self._parse_work(results[0])

    @staticmethod
    def _parse_work(work: Mapping[str, Any]) -> OpenAlexPaper:
        authorships = work.get("authorships") or []
        authors: list[str] = []
        for authorship in authorships:
            author = authorship.get("author") or {}
            name = author.get("display_name")
            if name:
                authors.append(name)

        abstract_index = work.get("abstract_inverted_index")
        abstract: str | None = None
        if abstract_index:
            try:
                abstract = invert_abstract(abstract_index)
            except Exception:
                abstract = None

        normalized: dict[str, Any] = {
            "paperId": work.get("id") or "",
            "title": work.get("display_name") or "",
            "abstract": abstract,
            "year": work.get("publication_year"),
            "authors": authors,
            "citationCount": work.get("cited_by_count"),
            "referenced_works": work.get("referenced_works") or [],
        }
        return OpenAlexPaper(**normalized)


def _parse_year_range(value: str | None) -> tuple[int, int] | None:
    if not value:
        return None
    parts = value.split("-")
    if len(parts) == 2 and all(part.isdigit() for part in parts):
        return int(parts[0]), int(parts[1])
    return None


@tool("openalex_search")
def openalex_search(
    query: str, year_range: str | None = None, limit: int = 5
) -> list[dict[str, Any]]:
    """Search OpenAlex for works matching a query."""

    settings = load_settings()
    api = OpenAlexAPI(mailto=settings.openalex_mailto)
    parsed_years = _parse_year_range(year_range)
    papers = api.search_papers(query, year_range=parsed_years, limit=limit)
    return [paper.model_dump() for paper in papers]


@tool("openalex_get_paper")
def openalex_get_paper(work_id: str) -> dict[str, Any]:
    """Fetch a single OpenAlex work by ID (or DOI)."""

    settings = load_settings()
    api = OpenAlexAPI(mailto=settings.openalex_mailto)
    paper = api.get_paper_details(work_id)
    return paper.model_dump()


__all__ = [
    "OpenAlexAPI",
    "OpenAlexPaper",
    "openalex_get_paper",
    "openalex_search",
]
