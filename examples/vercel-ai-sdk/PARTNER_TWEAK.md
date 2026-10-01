# Partner tweak guide — add a tool & configure the router

This playground is meant to be **edited**, not only clicked. Hosted invite
(`https://webrouter-aisdk.exe.xyz/`) proves live search + extract with keys.
This doc is how you change the *integration surface* after you clone the
monorepo (or edit on a VM with shell access).

Claim-safe: Layer-1 typed web-context; demo tools are search + extract;
preview / invite-gated; install via vendored wheel (no public PyPI live path).

## Where the integration lives

| File | Role |
|---|---|
| [`demo/tools.py`](demo/tools.py) | `build_tools(WebRouter())` → `[web_search, web_extract]` as `@ai.tool` |
| [`webapp/main.py`](webapp/main.py) | FastAPI + SSE chat; `router = WebRouter()` singleton |
| [`demo/env.py`](demo/env.py) | Keys: BYOK Session keys / `.env`, or host process-env (invite) |

Host pattern stays the same: wrap WebRouter behind ordinary AI SDK tools.
No fork of `ai`, no fork of `web_router`.

## Keys (do not commit secrets)

| Mode | Who | How |
|---|---|---|
| **(a) BYOK** | You | `.env` from `.env.example`, or **Session keys** in the web UI |
| **(b) Nimble-hosted invite** | Host ops | Process env on the private VM (`override=False` → host wins) |

Never put real keys in git. Invite keys are session-scoped for that private host.

## Configure the router

`WebRouter` accepts a default provider and optional per-provider constructor kwargs:

```python
from web_router import WebRouter

# Default every search/extract to Nimble unless the call overrides provider=
router = WebRouter(provider="nimble")

# Or pass provider-specific constructor options (credentials belong in env;
# provider_config is for timeouts / explicit kwargs when you need them):
router = WebRouter(
    provider="auto",
    provider_config={
        "nimble": {"timeout": 30},
        # "tavily": {"timeout": 20},
    },
)
```

In the web app, change the singleton near the top of `webapp/main.py`:

```python
router = WebRouter(provider="nimble")
```

The chat UI **provider dropdown** still passes a per-turn `provider` into
`build_tools(router, provider=…)`, which overrides on each tool call. So you
can pin a host default *and* let partners try auto / nimble / tavily / exa
from the UI.

Restart uvicorn after changing the singleton.

## Add another tool

`build_tools` returns a list of `@ai.tool` callables. Append your own; keep
using the same `WebRouter` instance (or call out when you intentionally leave
WebRouter).

Minimal sketch — a thin helper that always searches via Nimble:

```python
@ai.tool
async def nimble_web_search(query: str, max_results: int = 5) -> dict:
    """Search via WebRouter forced to the nimble provider."""
    outcome = await asyncio.to_thread(run_search, router, query, "nimble", max_results)
    return {
        "provider": outcome.provider,
        "query": outcome.query,
        "results": [
            {"title": h.title, "url": h.url, "description": h.description}
            for h in outcome.hits
        ],
    }

# In build_tools:
return [web_search, web_extract, nimble_web_search]
```

Wire the new tool into the agent the same way — `ai.Agent(tools=build_tools(...))`
already takes whatever `build_tools` returns (`webapp/main.py` stream path).

Tips:

- Keep tool docstrings clear; the model uses them to decide when to call.
- Prefer returning small JSON-friendly dicts (title/url/preview), not huge blobs.
- Stay claim-safe: if you add non–web-context tools, label them as your demo
  extras, not as WebRouter APIs.

See the commented sketch at the bottom of `demo/tools.py`.

## Local loop after a tweak

```bash
cd examples/vercel-ai-sdk
uv sync
uv run uvicorn webapp.main:app --host 127.0.0.1 --port 8811
# or: uv run python demo_terminal.py
```

On the invite VM, host ops remount from this monorepo tree
(`cwd = examples/vercel-ai-sdk`). Product edits land here first, then remount.

## Related

- [`PARTNER_30S.md`](PARTNER_30S.md) — 30-second chat walkthrough
- [`README.md`](README.md) — keys, run, integration surface
