"""Web Router wrapped as Vercel AI SDK (Python) tools.

This is the entire integration surface: two `@ai.tool` functions that call
`WebRouter.search` / `WebRouter.extract` on a background thread. No fork of
`ai`, no fork of `web_router` — just the adapter pattern from
AI_SDK_PYTHON_WEB_ROUTER_GUIDE.md.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

import ai
from web_router import WebRouter

PREVIEW_CHARS = 1500


@dataclass(frozen=True)
class SearchHit:
    title: str
    url: str
    description: str


@dataclass(frozen=True)
class SearchOutcome:
    provider: str
    query: str
    hits: list[SearchHit]
    answer: str | None
    elapsed_ms: int


@dataclass(frozen=True)
class ExtractOutcome:
    provider: str
    url: str
    title: str | None
    content: str
    truncated: bool
    elapsed_ms: int


def run_search(router: WebRouter, query: str, provider: str | None, max_results: int = 5) -> SearchOutcome:
    import time

    started = time.perf_counter()
    kwargs = {"max_results": max_results}
    if provider and provider != "auto":
        kwargs["provider"] = provider
    response = router.search(query, **kwargs)
    elapsed = int((time.perf_counter() - started) * 1000)
    hits = [
        SearchHit(title=r.title or "(untitled)", url=r.url, description=(r.description or "")[:200])
        for r in response.results
    ]
    return SearchOutcome(
        provider=response.provider,
        query=query,
        hits=hits,
        answer=response.answer,
        elapsed_ms=elapsed,
    )


def run_extract(router: WebRouter, url: str, provider: str | None, fmt: str = "markdown") -> ExtractOutcome:
    import time

    started = time.perf_counter()
    kwargs = {"format": fmt}
    if provider and provider != "auto":
        kwargs["provider"] = provider
    response = router.extract(url, **kwargs)
    elapsed = int((time.perf_counter() - started) * 1000)
    docs = response.documents or []
    content = (docs[0].content if docs else "") or ""
    title = docs[0].title if docs else None
    truncated = len(content) > PREVIEW_CHARS
    return ExtractOutcome(
        provider=response.provider,
        url=url,
        title=title,
        content=content[:PREVIEW_CHARS],
        truncated=truncated,
        elapsed_ms=elapsed,
    )


def build_tools(router: WebRouter, provider: str | None = None) -> list:
    """Return `[web_search, web_extract]` bound to a provider (or 'auto')."""

    @ai.tool
    async def web_search(query: str, max_results: int = 5) -> dict:
        """Search the web via web-router (multi-provider: nimble, tavily, exa, auto)."""
        outcome = await asyncio.to_thread(run_search, router, query, provider, max_results)
        return {
            "provider": outcome.provider,
            "query": outcome.query,
            "answer": outcome.answer,
            "results": [
                {"title": h.title, "url": h.url, "description": h.description} for h in outcome.hits
            ],
        }

    @ai.tool
    async def web_extract(url: str) -> dict:
        """Extract a URL as markdown via web-router (multi-provider: nimble, tavily, jina)."""
        outcome = await asyncio.to_thread(run_extract, router, url, provider)
        return {
            "provider": outcome.provider,
            "url": outcome.url,
            "title": outcome.title,
            "content_preview": outcome.content,
            "truncated": outcome.truncated,
        }

    return [web_search, web_extract]


# --- Partner tweak sketch (not wired into build_tools by default) ---
# To add another tool: define an @ai.tool like web_search / web_extract above,
# append it to the list returned by build_tools, restart uvicorn.
# To pin the router default / provider_config, change WebRouter(...) in
# webapp/main.py — see PARTNER_TWEAK.md.

