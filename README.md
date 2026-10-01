# web-router-playground

Monorepo of **WebRouter** integration playgrounds. Each entry under `examples/*` shows how a host framework can call WebRouter’s typed web-context tools (`search` + `extract`) without forking either package. More frameworks can land beside the first one — this repo is not AI-SDK-only forever.

> **Preview — not an official product launch.** APIs, packaging, and docs may change. There is no public PyPI release for WebRouter yet; use the **vendored wheel** in each example (do not `pip install web-router` from PyPI as the live path).

## Playgrounds

| Playground | Path | Host |
|---|---|---|
| Vercel AI SDK (Python) | [`examples/vercel-ai-sdk/`](examples/vercel-ai-sdk/) | Vercel AI SDK for Python (`@ai.tool` / `build_tools(WebRouter())`) |

Room for more: add a sibling under `examples/<framework>/` with its own README, vendored wheel (or shared vendor policy), and `.env.example`. Keep claim-safe language (Layer-1 / typed web-context; search + extract only).

**Hosted sandbox (invite-gated):** Exe.dev VM `webrouter-aisdk` → `https://webrouter-aisdk.exe.xyz/`. Not open to the anonymous public web — partners get invite / auth from the host. The *running* sandbox is this monorepo’s `examples/vercel-ai-sdk` tree (not a loose zip fork). Public clone = code showcase; live keys stay on the private invite session.

### Exe deploy SoT (host-ops)

When remounting the invite VM from this monorepo:

```text
cwd:   web-router-playground/examples/vercel-ai-sdk
start: uv run uvicorn webapp.main:app --host 0.0.0.0 --port 8811
```

`demo/env.py` loads `.env` with `override=False`, so **host process env wins** over a file `.env`. That is how Nimble-hosted invite keys work without committing secrets.

## Keys — two modes (never commit real keys)

| Mode | Who | How | Where keys live |
|---|---|---|---|
| **(a) BYOK** | Partner | Copy `.env.example` → `.env` and paste keys, **or** use the in-app session paste panel on the web UI | Local `.env` (gitignored) and/or process env for that run |
| **(b) Nimble-hosted session** | Host (Exe / Nimble ops) | Inject keys into the **process environment** on the private invite VM before/while uvicorn runs | Host process env only — never public, never shared across guests, never in git |

- Keep **`.env.example` only** in git (empty placeholders). Never commit `.env` or real keys.
- No public shared keys. Invite VM keys are session-scoped for that private host.
- Optional providers (Tavily, Exa, …) depend on which keys you have; Jina extract can run keyless for the demo tier. Nimble is a founding peer provider.

## Direction (claim-safe)

- **Layer-1 / typed web-context** as the integration direction
- Demo surface is **search + extract only** (browser / web context live in the UI)
- Host pattern: `@ai.tool` wrapping `build_tools(WebRouter())`
- First playground host: Vercel AI SDK for Python — more hosts welcome under `examples/*`
- Install via **vendored wheel** in each example (`vendor/*.whl`)

## Layout

```
web-router-playground/
  README.md                 ← you are here
  examples/
    README.md
    vercel-ai-sdk/          ← first playground (web UI + terminal)
    # <next-framework>/     ← future playgrounds
  .gitignore
```

## Local run (optional)

Prefer the invite URL when you have access. To run from clone:

```bash
cd examples/vercel-ai-sdk
cp .env.example .env   # mode (a): add your keys
uv sync                # pulls web-router from vendor/*.whl
uv run python demo_terminal.py
# or web UI:
uv run uvicorn webapp.main:app --host 127.0.0.1 --port 8811
```

See [`examples/vercel-ai-sdk/README.md`](examples/vercel-ai-sdk/README.md) for partner UX detail and the 30-second walkthrough.
