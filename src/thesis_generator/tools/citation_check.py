from __future__ import annotations

import os
from typing import Any, Mapping

import requests

from thesis_generator.config import load_settings

SCITE_TALLIES_URL = "https://api.scite.ai/tallies"


class SciteError(Exception):
    """Base Scite error."""


class RateLimitError(SciteError):
    """Raised when Scite returns 429."""


class CoverageError(SciteError):
    """Raised when Scite has no coverage for the DOI."""


class SciteClient:
    """Lightweight client for Scite tallies."""

    def __init__(
        self,
        api_key: str,
        *,
        session: requests.Session | None = None,
        base_url: str = SCITE_TALLIES_URL,
    ) -> None:
        self.api_key = api_key
        self.session = session or requests.Session()
        self.base_url = base_url.rstrip("/")

    def _fetch_tallies(self, doi: str) -> dict[str, int]:
        url = f"{self.base_url}/{doi}"
        headers = {"x-api-key": self.api_key}
        response = self.session.get(url, headers=headers, timeout=10)

        if response.status_code == 429:
            raise RateLimitError("Scite API rate limit reached")
        if response.status_code == 404:
            raise CoverageError("Scite has no coverage for this DOI")

        try:
            response.raise_for_status()
        except Exception as exc:
            raise SciteError("Scite API error") from exc

        payload: Mapping[str, Any] = response.json()
        tallies = payload.get("tallies") if isinstance(payload, Mapping) else None
        if not tallies:
            raise SciteError("Scite response missing tallies")

        return {
            "supporting": int(tallies.get("supporting", 0) or 0),
            "mentioning": int(tallies.get("mentioning", 0) or 0),
            "contrasting": int(tallies.get("contrasting", 0) or 0),
        }

    @staticmethod
    def _compute_trust_score(tallies: Mapping[str, int]) -> float:
        supporting = tallies.get("supporting", 0)
        mentioning = tallies.get("mentioning", 0)
        contrasting = tallies.get("contrasting", 0)

        total = supporting + mentioning + contrasting
        if total == 0:
            return 0.0
        return round((supporting + 0.5 * mentioning) / total, 3)

    def _fallback(self, doi: str, message: str, reason: str) -> dict[str, Any]:
        return {
            "doi": doi,
            "supporting": 0,
            "mentioning": 0,
            "contrasting": 0,
            "trust_score": 0.0,
            "warning": message,
            "source": "fallback",
            "reason": reason,
            "manual_review_required": True,
        }

    def evaluate_doi(self, doi: str) -> dict[str, Any]:
        """Fetch tallies for a DOI and compute a trust score with warnings."""

        try:
            tallies = self._fetch_tallies(doi)
        except RateLimitError as exc:
            return self._fallback(doi, f"{exc}. Manual approval or alternate source required.", "rate_limit")
        except CoverageError as exc:
            return self._fallback(doi, f"{exc}. Please verify manually or use alternative source.", "coverage")
        except Exception as exc:
            return self._fallback(doi, f"Scite error: {exc}", "error")

        trust_score = self._compute_trust_score(tallies)
        warning: str | None = None

        if sum(tallies.values()) == 0:
            warning = "Scite coverage is empty; manual verification recommended."
        elif tallies["contrasting"] > tallies["supporting"]:
            warning = "contrasting evidence exceeds supporting citations."

        return {
            "doi": doi,
            "supporting": tallies["supporting"],
            "mentioning": tallies["mentioning"],
            "contrasting": tallies["contrasting"],
            "trust_score": trust_score,
            "warning": warning,
            "source": "scite",
            "manual_review_required": warning is not None,
        }


def _resolve_api_key(provided: str | None) -> str:
    if provided:
        return provided
    env_key = os.getenv("SCITE_API_KEY")
    if env_key:
        return env_key

    try:
        settings = load_settings()
    except RuntimeError as exc:
        raise RuntimeError("SCITE_API_KEY is not configured") from exc
    return settings.scite_api_key


def check_citations(
    dois: list[str], *, session: requests.Session | None = None, api_key: str | None = None
) -> list[dict[str, Any]]:
    """Evaluate a list of DOIs via Scite, applying fallbacks when unavailable."""

    resolved_key = _resolve_api_key(api_key)
    client = SciteClient(api_key=resolved_key, session=session)
    return [client.evaluate_doi(doi) for doi in dois]


__all__ = ["SciteClient", "check_citations"]
