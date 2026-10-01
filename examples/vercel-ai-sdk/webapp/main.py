"""FastAPI backend for the Web Router x AI SDK playground.

One route renders the UI, one route streams an agent turn as Server-Sent
Events so the browser can show tool calls the moment they start, not after
the whole response finishes. Session-keys endpoint lets partners paste BYOK
into process env for this run (never written to disk / git).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import AsyncIterator

import ai
from fastapi import FastAPI
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from web_router import WebRouter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from demo.env import (
    apply_session_keys,
    configured_providers,
    configured_status,
    has_openai_key,
    load_env,
)
from demo.tools import build_tools

load_env()

app = FastAPI(title="Web Router x AI SDK demo")
STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

router = WebRouter()


class ChatRequest(BaseModel):
    message: str
    provider: str = "auto"


class SessionKeysRequest(BaseModel):
    """BYOK paste — empty fields ignored; does not clear host-injected keys."""

    NIMBLE_API_KEY: str = Field(default="")
    TAVILY_API_KEY: str = Field(default="")
    EXA_API_KEY: str = Field(default="")
    OPENAI_API_KEY: str = Field(default="")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/providers")
def providers() -> dict:
    return {
        "search_extract": configured_providers(),
        "openai": has_openai_key(),
        "status": configured_status(),
    }


@app.post("/api/session-keys")
def session_keys(req: SessionKeysRequest) -> dict:
    """Apply partner keys to process env for this uvicorn process only.

    Mode (a) BYOK. Mode (b) Nimble-hosted keys should be injected by the host
    into process env before start; this endpoint never writes `.env` or logs
    values.
    """
    status = apply_session_keys(req.model_dump())
    return {
        "ok": True,
        "search_extract": {
            "nimble": status["nimble"],
            "tavily": status["tavily"],
            "exa": status["exa"],
        },
        "openai": status["openai"],
        "status": status,
    }


def sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


async def stream_agent_turn(message: str, provider: str) -> AsyncIterator[str]:
    if not has_openai_key():
        yield sse(
            "error",
            {
                "message": (
                    "OPENAI_API_KEY is not configured. Paste keys via Session keys "
                    "(BYOK) or ask the host to inject invite-session env."
                )
            },
        )
        return

    tools = build_tools(router, provider=provider)
    agent = ai.Agent(tools=tools)
    model = ai.get_model("openai:gpt-4o-mini")
    messages = [ai.user_message(message)]

    try:
        async with agent.run(model, messages) as stream:
            async for event in stream:
                kind = event.kind
                if kind == "tool_start":
                    yield sse("tool_start", {"name": event.tool_name, "call_id": event.tool_call_id})
                elif kind == "tool_end":
                    yield sse(
                        "tool_args",
                        {"call_id": event.tool_call_id, "args": event.tool_call.tool_args},
                    )
                elif kind == "tool_call_result":
                    for part in event.results:
                        yield sse(
                            "tool_result",
                            {
                                "call_id": part.tool_call_id,
                                "name": part.tool_name,
                                "result": part.result,
                            },
                        )
                elif kind == "text_delta":
                    yield sse("text_delta", {"chunk": event.chunk})
    except Exception as exc:  # noqa: BLE001 - surface the error to the UI
        yield sse("error", {"message": str(exc)})
        return

    yield sse("done", {})


@app.post("/api/chat")
async def chat(req: ChatRequest) -> StreamingResponse:
    return StreamingResponse(
        stream_agent_turn(req.message, req.provider),
        media_type="text/event-stream",
    )
