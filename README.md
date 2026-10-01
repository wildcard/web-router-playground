# web-router-playground

Monorepo of **WebRouter** integration playgrounds. Each example shows how a host framework can call WebRouter’s typed web-context tools (`search` + `extract`) without forking either package.

> **Preview — not an official product launch.** APIs, packaging, and docs may change. There is no public PyPI release for WebRouter yet; use the **vendored wheel** in each example (do not `pip install web-router` from PyPI as the live path).

## First playground

| Playground | Path | Host |
|---|---|---|
| Vercel AI SDK (Python) | [`examples/vercel-ai-sdk/`](examples/vercel-ai-sdk/) | Vercel AI SDK for Python (`@ai.tool` / `build_tools(WebRouter())`) |

**Hosted sandbox:** invite-gated on Exe.dev (`webrouter-aisdk` / `https://webrouter-aisdk.exe.xyz/`). Not open to the anonymous public web — partners get an invite / auth access from the host. Cloning this repo is the public code showcase; the *running* sandbox with any live keys stays gated.

## Bring your own keys

Guests supply their own API keys. Copy `.env.example` → `.env` inside the example you run. Never commit `.env`.

Nimble is a founding peer provider; other search/extract adapters in the demo are optional depending on which keys you have.

## Direction (claim-safe)

- **Layer-1 / typed web-context** as the integration direction
- Demo surface is **search + extract only**
- Host pattern: `@ai.tool` wrapping `build_tools(WebRouter())`
- Vercel AI SDK as the host framework for the first playground
- Install via **vendored wheel** in the example zip/clone

## Layout

```
web-router-playground/
  README.md                 ← you are here
  examples/
    README.md
    vercel-ai-sdk/          ← first playground (from preview pack)
  .gitignore
```

## Local run (optional)

If you prefer clone over the hosted URL, see [`examples/vercel-ai-sdk/README.md`](examples/vercel-ai-sdk/README.md). Typical flow:

```bash
cd examples/vercel-ai-sdk
cp .env.example .env   # add your keys
uv sync                # pulls web-router from vendor/*.whl
uv run python demo_terminal.py
# or: uv run uvicorn webapp.main:app --host 127.0.0.1 --port 8811
```
