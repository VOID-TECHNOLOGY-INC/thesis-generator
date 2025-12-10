from __future__ import annotations

import os
from collections.abc import Callable, Iterable, Mapping, Sequence
from typing import Any

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
            return self._fallback(
                doi,
                f"{exc}. Manual approval or alternate source required.",
                "rate_limit",
            )
        except CoverageError as exc:
            return self._fallback(
                doi,
                f"{exc}. Please verify manually or use alternative source.",
                "coverage",
            )
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


def _maybe_resolve_api_key(provided: str | None) -> str | None:
    if provided:
        return provided
    env_key = os.getenv("SCITE_API_KEY")
    if env_key:
        return env_key
    return None


def check_citations(
    dois: list[str], *, session: requests.Session | None = None, api_key: str | None = None
) -> list[dict[str, Any]]:
    """Evaluate a list of DOIs via Scite, applying fallbacks when unavailable."""

    resolved_key = _resolve_api_key(api_key)
    client = SciteClient(api_key=resolved_key, session=session)
    return [client.evaluate_doi(doi) for doi in dois]


def _tally_labels(labels: Iterable[str]) -> dict[str, int]:
    tallies = {"supporting": 0, "mentioning": 0, "contrasting": 0}
    for raw in labels:
        label = (raw or "").strip().lower()
        if label in tallies:
            tallies[label] += 1
        else:
            tallies["mentioning"] += 1
    return tallies


def _default_fetch_contexts(_: str) -> list[str]:
    return []


def _default_classify(contexts: Sequence[str]) -> list[str]:
    labels: list[str] = []
    for text in contexts:
        lower = text.lower()
        if any(token in lower for token in ("refute", "contradict", "contrast")):
            labels.append("contrasting")
        elif "support" in lower:
            labels.append("supporting")
        else:
            labels.append("mentioning")
    return labels


def evaluate_citations_with_fallback(
    dois: Sequence[str],
    *,
    scite_api_key: str | None = None,
    session: requests.Session | None = None,
    fetch_contexts: Callable[[str], Sequence[str]] | None = None,
    classify_fn: Callable[[Sequence[str]], Sequence[str]] | None = None,
) -> list[dict[str, Any]]:
    """Evaluate DOIs using Scite when available, otherwise LLM-based stance classification.

    - If a Scite API key is resolved, use SciteClient first.
    - If Scite is unavailable or fails, fetch citation contexts (OpenAlex/S2/COCI, etc.)
      and classify them into supporting/mentioning/contrasting labels via the provided classifier.
    - Missing contexts or failures yield a warning and require manual review.
    """

    scite_key = _maybe_resolve_api_key(scite_api_key)
    scite_client: SciteClient | None = None
    if scite_key:
        scite_client = SciteClient(api_key=scite_key, session=session)

    results: list[dict[str, Any]] = []
    fetcher = fetch_contexts or _default_fetch_contexts
    classifier = classify_fn or _default_classify

    for doi in dois:
        scite_warning: str | None = None
        if scite_client:
            try:
                results.append(scite_client.evaluate_doi(doi))
                continue
            except Exception as exc:
                scite_warning = f"Scite unavailable: {exc}"

        try:
            contexts = list(fetcher(doi))
        except Exception as exc:  # pragma: no cover - error path asserted via warning
            results.append(
                {
                    "doi": doi,
                    "supporting": 0,
                    "mentioning": 0,
                    "contrasting": 0,
                    "trust_score": 0.0,
                    "warning": f"Failed to fetch citation contexts: {exc}",
                    "source": "llm_fallback",
                    "manual_review_required": True,
                }
            )
            continue

        if not contexts:
            warning = scite_warning or "No citation contexts available"
            results.append(
                {
                    "doi": doi,
                    "supporting": 0,
                    "mentioning": 0,
                    "contrasting": 0,
                    "trust_score": 0.0,
                    "warning": warning,
                    "source": "llm_fallback",
                    "manual_review_required": True,
                }
            )
            continue

        try:
            labels = list(classifier(contexts))
        except Exception as exc:  # pragma: no cover - defensive
            results.append(
                {
                    "doi": doi,
                    "supporting": 0,
                    "mentioning": 0,
                    "contrasting": 0,
                    "trust_score": 0.0,
                    "warning": f"Classification failed: {exc}",
                    "source": "llm_fallback",
                    "manual_review_required": True,
                }
            )
            continue

        tallies = _tally_labels(labels)
        trust_score = SciteClient._compute_trust_score(tallies)
        results.append(
            {
                "doi": doi,
                "supporting": tallies["supporting"],
                "mentioning": tallies["mentioning"],
                "contrasting": tallies["contrasting"],
                "trust_score": trust_score,
                "warning": scite_warning,
                "source": "llm_fallback",
                "manual_review_required": False,
            }
        )

    return results


__all__ = ["SciteClient", "check_citations"]
