from __future__ import annotations

import asyncio
from dataclasses import dataclass
import re
from typing import Any
from urllib.parse import parse_qs, quote_plus, unquote, urlparse

try:
    import httpx
except ImportError:  # pragma: no cover
    httpx = None


@dataclass
class SuggestionItem:
    text: str
    url: str


@dataclass
class SuggestionPanel:
    source: str
    suggestions: list[SuggestionItem]
    error: str | None = None


GOOGLE_URL = "https://suggestqueries.google.com/complete/search"
YOUTUBE_URL = "https://suggestqueries.google.com/complete/search"
BING_URL = "https://api.bing.com/osjson.aspx"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}

GOOGLE_SEARCH_URL = "https://www.google.com/search"
YOUTUBE_RESULTS_URL = "https://www.youtube.com/results"
BING_SEARCH_URL = "https://www.bing.com/search"
DUCKDUCKGO_HTML_URL = "https://html.duckduckgo.com/html/"

GOOGLE_RESULT_RE = re.compile(r'href="/url\?q=(https?://[^"&]+)')
BING_RESULT_RE = re.compile(r'<li class="b_algo".*?<h2><a href="(https?://[^"]+)"', re.DOTALL)
YOUTUBE_VIDEO_RE = re.compile(r'"videoId":"([A-Za-z0-9_-]{11})"')
DDG_RESULT_RE = re.compile(r'nofollow" class="result__a" href="([^"]+)"')


def _normalize(items: list[Any]) -> list[str]:
    seen: set[str] = set()
    normalized: list[str] = []
    for item in items:
        value = str(item).strip()
        if value and value.lower() not in seen:
            normalized.append(value)
            seen.add(value.lower())
    return normalized


def _fallback_search_url(source: str, query: str) -> str:
    encoded = quote_plus(query)
    source_map = {
        "Google": f"{GOOGLE_SEARCH_URL}?q={encoded}",
        "YouTube": f"{YOUTUBE_RESULTS_URL}?search_query={encoded}",
        "Bing": f"{BING_SEARCH_URL}?q={encoded}",
    }
    return source_map.get(source, "#")


def _clean_google_result(url: str) -> str:
    parsed = urlparse(unquote(url))
    if parsed.netloc.endswith("google.com") and parsed.path == "/url":
        target = parse_qs(parsed.query).get("q", [""])[0]
        return target or url
    return unquote(url)


def _clean_duckduckgo_result(url: str) -> str:
    decoded = unquote(url)
    parsed = urlparse(decoded)
    if "duckduckgo.com" in parsed.netloc and parsed.path.startswith("/l/"):
        target = parse_qs(parsed.query).get("uddg", [""])[0]
        return unquote(target) or decoded
    return decoded


async def _resolve_google_result(client: httpx.AsyncClient, query: str) -> str:
    try:
        response = await client.get(GOOGLE_SEARCH_URL, params={"q": query, "hl": "uz"})
        response.raise_for_status()
        match = GOOGLE_RESULT_RE.search(response.text)
        if match:
            return _clean_google_result(match.group(1))
    except Exception:
        pass
    return _fallback_search_url("Google", query)


async def _resolve_bing_result(client: httpx.AsyncClient, query: str) -> str:
    try:
        response = await client.get(BING_SEARCH_URL, params={"q": query})
        response.raise_for_status()
        match = BING_RESULT_RE.search(response.text)
        if match:
            return unquote(match.group(1))
    except Exception:
        pass
    return _fallback_search_url("Bing", query)


async def _resolve_duckduckgo_result(client: httpx.AsyncClient, query: str) -> str | None:
    try:
        response = await client.get(DUCKDUCKGO_HTML_URL, params={"q": query})
        response.raise_for_status()
        match = DDG_RESULT_RE.search(response.text)
        if match:
            return _clean_duckduckgo_result(match.group(1))
    except Exception:
        pass
    return None


async def _resolve_youtube_result(client: httpx.AsyncClient, query: str) -> str:
    try:
        response = await client.get(YOUTUBE_RESULTS_URL, params={"search_query": query, "hl": "uz"})
        response.raise_for_status()
        match = YOUTUBE_VIDEO_RE.search(response.text)
        if match:
            return f"https://www.youtube.com/watch?v={match.group(1)}"
    except Exception:
        pass
    return _fallback_search_url("YouTube", query)


async def _build_items(
    client: httpx.AsyncClient,
    source: str,
    suggestions: list[str],
) -> list[SuggestionItem]:
    if source == "YouTube":
        urls = await asyncio.gather(*(_resolve_youtube_result(client, item) for item in suggestions))
    else:
        primary_resolver = _resolve_google_result if source == "Google" else _resolve_bing_result
        primary_urls = await asyncio.gather(*(primary_resolver(client, item) for item in suggestions))
        ddg_urls = await asyncio.gather(*(_resolve_duckduckgo_result(client, item) for item in suggestions))
        urls = []
        for item, primary_url, ddg_url in zip(suggestions, primary_urls, ddg_urls):
            fallback = _fallback_search_url(source, item)
            chosen = ddg_url or (primary_url if primary_url != fallback else "")
            urls.append(chosen or primary_url)
    return [SuggestionItem(text=text, url=url) for text, url in zip(suggestions, urls)]


async def _fetch_google(client: httpx.AsyncClient, query: str) -> SuggestionPanel:
    try:
        response = await client.get(
            GOOGLE_URL,
            params={"client": "firefox", "q": query, "hl": "uz"},
        )
        response.raise_for_status()
        payload = response.json()
        suggestions = _normalize(payload[1])
        return SuggestionPanel(
            source="Google",
            suggestions=await _build_items(client, "Google", suggestions),
        )
    except Exception as exc:
        return SuggestionPanel(source="Google", suggestions=[], error=str(exc))


async def _fetch_youtube(client: httpx.AsyncClient, query: str) -> SuggestionPanel:
    try:
        response = await client.get(
            YOUTUBE_URL,
            params={"client": "firefox", "ds": "yt", "q": query, "hl": "uz"},
        )
        response.raise_for_status()
        payload = response.json()
        suggestions = _normalize(payload[1])
        return SuggestionPanel(
            source="YouTube",
            suggestions=await _build_items(client, "YouTube", suggestions),
        )
    except Exception as exc:
        return SuggestionPanel(source="YouTube", suggestions=[], error=str(exc))


async def _fetch_bing(client: httpx.AsyncClient, query: str) -> SuggestionPanel:
    try:
        response = await client.get(BING_URL, params={"query": query, "market": "en-US"})
        response.raise_for_status()
        payload = response.json()
        suggestions = _normalize(payload[1])
        return SuggestionPanel(
            source="Bing",
            suggestions=await _build_items(client, "Bing", suggestions),
        )
    except Exception as exc:
        return SuggestionPanel(source="Bing", suggestions=[], error=str(exc))


async def fetch_suggestions(query: str) -> list[SuggestionPanel]:
    if httpx is None:
        return [
            SuggestionPanel(
                source="Google",
                suggestions=[],
                error="`httpx` o'rnatilmagan. `pip install -r requirements.txt` ni ishga tushiring.",
            ),
            SuggestionPanel(
                source="YouTube",
                suggestions=[],
                error="`httpx` o'rnatilmagan. `pip install -r requirements.txt` ni ishga tushiring.",
            ),
            SuggestionPanel(
                source="Bing",
                suggestions=[],
                error="`httpx` o'rnatilmagan. `pip install -r requirements.txt` ni ishga tushiring.",
            ),
        ]
    async with httpx.AsyncClient(headers=HEADERS, timeout=10.0, follow_redirects=True) as client:
        return await asyncio.gather(
            _fetch_google(client, query),
            _fetch_youtube(client, query),
            _fetch_bing(client, query),
        )
