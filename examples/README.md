# Examples

Integration playgrounds for WebRouter. Preview only — not an official launch.

Each subdirectory is a **host-framework playground**: same Layer-1 story (typed web-context, `search` + `extract`), different SDK. Add new frameworks as siblings; do not treat this folder as AI-SDK-only forever.

| Playground | Directory | Host framework | Notes |
|---|---|---|---|
| Vercel AI SDK (Python) | [`vercel-ai-sdk/`](vercel-ai-sdk/) | Vercel AI SDK for Python | Live web UI + terminal; `@ai.tool` / `build_tools(WebRouter())`; vendored wheel under `vendor/` |

**Hosted Exe.dev sandbox** (`https://webrouter-aisdk.exe.xyz/`) is **invite-gated**, not anonymous-public. Deploy SoT cwd is `examples/vercel-ai-sdk` with `uv run uvicorn webapp.main:app --host 0.0.0.0 --port 8811`. Partners: bring your own keys (`.env` from `.env.example`, or in-app session paste). Hosts: inject Nimble session keys via process env on the private VM (`load_env` uses `override=False` so host env wins). Never commit `.env`.
