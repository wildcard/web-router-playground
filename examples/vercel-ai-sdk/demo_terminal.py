#!/usr/bin/env python
"""Terminal demo: Web Router x Vercel AI SDK (Python).

Three acts:
  1. Multi-provider search — same query, different backends, one response shape.
  2. Multi-provider extract — same URL, different backends, one response shape.
  3. An AI SDK agent that calls `web_search` / `web_extract` as tools to answer
     a question end to end, streaming its tool calls and final answer live.

Run:
    uv run python demo_terminal.py
"""

from __future__ import annotations

import asyncio
import sys
import time

import ai
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from web_router import WebRouter

from demo.env import configured_providers, has_openai_key, load_env
from demo.tools import build_tools, run_extract, run_search

ZINC = "grey62"
DIM = "grey42"
BRIGHT = "bright_white"

console = Console(highlight=False)

SEARCH_QUERY = "retrieval augmented generation"
EXTRACT_URL = "https://en.wikipedia.org/wiki/Retrieval-augmented_generation"
AGENT_QUESTION = (
    "Search for the Nimble web-router Python package, then extract the top result "
    "and summarize in two sentences what problem it solves."
)


def banner() -> None:
    title = Text("WebRouter", style=f"bold {BRIGHT}")
    title.append("  x  ", style=DIM)
    title.append("Vercel AI SDK (Python)", style=f"bold {BRIGHT}")
    console.print()
    console.print(Panel(title, border_style=ZINC, padding=(1, 4), expand=False))
    console.print(
        Text("one integration, every search & extract provider", style=f"italic {DIM}"),
        justify="left",
    )
    console.print()


def provider_status() -> None:
    table = Table(border_style=ZINC, header_style=f"bold {BRIGHT}", box=None, pad_edge=False)
    table.add_column("provider")
    table.add_column("status")
    for name, ok in configured_providers().items():
        status = Text("configured", style="bold green") if ok else Text("keyless tier", style=DIM)
        table.add_row(Text(name, style=BRIGHT), status)
    table.add_row(Text("openai", style=BRIGHT), Text("configured", style="bold green") if has_openai_key() else Text("missing", style="bold red"))
    console.print(table)
    console.print()


def act_search(router: WebRouter) -> None:
    console.rule(Text("Act I — one query, every search provider", style=f"bold {BRIGHT}"), style=ZINC)
    console.print()
    for provider in ("nimble", "tavily", "exa", "auto"):
        try:
            outcome = run_search(router, SEARCH_QUERY, provider, max_results=3)
        except Exception as exc:  # noqa: BLE001 - demo resilience, not library code
            console.print(f"  [{DIM}]{provider:>8}[/{DIM}]  [red]skipped — {exc}[/red]")
            continue
        top = outcome.hits[0] if outcome.hits else None
        resolved = f"{provider} -> {outcome.provider}" if provider == "auto" else outcome.provider
        console.print(
            f"  [{BRIGHT}]{resolved:<16}[/{BRIGHT}] [{DIM}]{outcome.elapsed_ms:>5}ms[/{DIM}]  "
            + (f"{top.title}" if top else "no results")
        )
        if top:
            console.print(f"  {'':<16} {'':>8}  [{DIM}]{top.url}[/{DIM}]")
    console.print()


def act_extract(router: WebRouter) -> None:
    console.rule(Text("Act II — one URL, every extract provider", style=f"bold {BRIGHT}"), style=ZINC)
    console.print()
    for provider in ("nimble", "tavily", "jina"):
        try:
            outcome = run_extract(router, EXTRACT_URL, provider)
        except Exception as exc:  # noqa: BLE001
            console.print(f"  [{DIM}]{provider:>8}[/{DIM}]  [red]skipped — {exc}[/red]")
            continue
        chars = len(outcome.content) if not outcome.truncated else f"{len(outcome.content)}+"
        console.print(
            f"  [{BRIGHT}]{provider:<16}[/{BRIGHT}] [{DIM}]{outcome.elapsed_ms:>5}ms[/{DIM}]  "
            f"{chars} chars  [{DIM}]{(outcome.title or '(no title)')[:60]}[/{DIM}]"
        )
    console.print()


async def act_agent(router: WebRouter) -> None:
    console.rule(Text("Act III — one agent, tools it never had to hand-roll", style=f"bold {BRIGHT}"), style=ZINC)
    console.print()
    console.print(f"[{DIM}]> {AGENT_QUESTION}[/{DIM}]")
    console.print()

    if not has_openai_key():
        console.print("[bold red]OPENAI_API_KEY missing — skipping live agent run.[/bold red]")
        return

    tools = build_tools(router, provider="nimble")
    agent = ai.Agent(tools=tools)
    model = ai.get_model("openai:gpt-4o-mini")
    messages = [ai.user_message(AGENT_QUESTION)]

    printed_tool_header = set()
    text_started = False
    async with agent.run(model, messages) as stream:
        async for event in stream:
            kind = event.kind
            if kind == "tool_start":
                name = event.tool_name
                if name not in printed_tool_header:
                    console.print(f"  [bold {BRIGHT}]tool call[/bold {BRIGHT}] [{ZINC}]{name}[/{ZINC}]", end="")
                    printed_tool_header.add(name)
            elif kind == "tool_end":
                console.print(f"  [{DIM}]{event.tool_call.tool_args}[/{DIM}]")
            elif kind == "tool_call_result":
                for part in event.results:
                    provider = (part.result or {}).get("provider", "?")
                    console.print(f"    [{DIM}]-> served by[/{DIM}] [bold green]{provider}[/bold green]")
            elif kind == "text_delta":
                if not text_started:
                    console.print()
                    console.print(f"  [bold {BRIGHT}]answer[/bold {BRIGHT}]")
                    text_started = True
                console.print(event.chunk, end="", style=BRIGHT)
    console.print()
    console.print()


async def main() -> None:
    load_env()
    banner()
    provider_status()

    with WebRouter() as router:
        act_search(router)
        act_extract(router)
        await act_agent(router)

    console.rule(style=ZINC)
    console.print(
        Text(
            "frameworks integrate once — providers maintain adapters — "
            "maintainers stop re-implementing every search SDK.",
            style=f"italic {DIM}",
        )
    )
    console.print()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(130)
