# Vercel AI SDK (Python)

**Live demo:** WebRouter `search` + `extract` (typed web-context / browser tools) plugged into the Vercel AI SDK for Python as ordinary `@ai.tool` functions. No fork of either package.

This directory is the first playground under the [`web-router-playground`](../../) monorepo. The invite-gated Exe sandbox runs **this tree** (cwd = here), not a loose zip fork.

## What you see in the web UI

- Branding: **web-router × Vercel AI SDK (Python)**
- Provider chips (nimble / tavily / exa / openai) — green when a key is available for this session
- Chat composer: ask anything that needs live web search, URL extract, or both
- Streaming tool cards: `web_search` / `web_extract` fire live; each card shows which provider **served** the call

Same story as the terminal demo (`demo_terminal.py`) — multi-provider search/extract, then an agent that uses those tools end-to-end.

## Keys — (a) BYOK and (b) Nimble-hosted session

| Mode | Audience | How |
|---|---|---|
| **(a) Bring your own keys** | Partners on invite VM or local clone | Copy `.env.example` → `.env` and fill keys, **or** open **Session keys** in the web UI and paste for this process only |
| **(b) Nimble-hosted session** | Host ops on the private invite VM only | Inject `NIMBLE_API_KEY` / `OPENAI_API_KEY` (and optional others) into the **process environment** before/while uvicorn runs. `demo/env.py` loads `.env` with `override=False`, so **host process env wins**. Never put real keys in git; never share one public key set |

Required for a full agent turn: `OPENAI_API_KEY` plus at least one search provider (Nimble recommended). Jina extract can run keyless for the demo tier. Optional: `TAVILY_API_KEY`, `EXA_API_KEY`.

`.env.example` is the only env template in git. Never commit `.env`.

## Requirements

- Python ≥ 3.12
- [`uv`](https://docs.astral.sh/uv/)
- Vendored `web-router` wheel under `vendor/` (no public PyPI live path)

## Run

```bash
# From monorepo root, or already inside this directory:
cp .env.example .env    # mode (a)
uv sync

# Terminal demo
uv run python demo_terminal.py

# Web UI — local
uv run uvicorn webapp.main:app --host 127.0.0.1 --port 8811

# Web UI — Exe invite VM (deploy SoT)
uv run uvicorn webapp.main:app --host 0.0.0.0 --port 8811
```

Invite URL (private): `https://webrouter-aisdk.exe.xyz/`

## Integration surface

The plug-in lives in `demo/tools.py` — `build_tools(WebRouter())` returns `[web_search, web_extract]`.

```python
from ai.agent import Agent
from web_router import WebRouter
from demo.tools import build_tools

agent = Agent(
    model="openai:gpt-4o-mini",
    tools=build_tools(WebRouter()),
)
```

Same agent. Swap the tools list. Providers stay behind adapters.

## Tweak the playground (add a tool / configure the router)

Partners who clone this tree (or edit on a shell-enabled invite VM) can change the integration — not only chat.

See **[`PARTNER_TWEAK.md`](PARTNER_TWEAK.md)** for:

- Pinning `WebRouter(provider=…, provider_config=…)` in `webapp/main.py`
- Adding another `@ai.tool` in `demo/tools.py` `build_tools`
- Local restart loop after edits

## Partner 30-second walkthrough

1. Open the invite link → land on the dark chat UI (**web-router × Vercel AI SDK**).
2. Confirm provider chips: green = keyed for this session (host-injected Nimble/OpenAI, or your BYOK paste).
3. Try a prompt, e.g. *“Search for retrieval-augmented generation, then extract the top Wikipedia result and summarize in two sentences.”*
4. Watch streaming **tool cards** for `web_search` / `web_extract` and the **served by \<provider\>** line — that is live WebRouter web-context, not a blank shell.
5. Optionally switch the provider dropdown (auto / nimble / tavily / exa) and send again.

Claim-safe: Layer-1 typed web-context; search + extract only; preview / invite-gated; vendored wheel.
