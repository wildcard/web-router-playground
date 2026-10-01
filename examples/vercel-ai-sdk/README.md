# Vercel AI SDK (Python)

Drop WebRouter `search` / `extract` into the Vercel AI SDK for Python as ordinary `@ai.tool` functions. No fork of either package.

## Requirements

- Python ≥ 3.12
- [`uv`](https://docs.astral.sh/uv/)
- Copy `.env.example` → `.env` and add keys you have (`NIMBLE_API_KEY`, `TAVILY_API_KEY`, `EXA_API_KEY`, `OPENAI_API_KEY`). Jina extract can run keyless.

The `web-router` wheel is vendored under `vendor/` so you do not need another repo.

## Run

```bash
cp .env.example .env
uv sync

# Terminal demo
uv run python demo_terminal.py

# Web UI — http://127.0.0.1:8811
uv run uvicorn webapp.main:app --host 127.0.0.1 --port 8811
```

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
