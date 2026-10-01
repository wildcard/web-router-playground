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
from demo.harness_defaults import DEFAULT_MAX_RESULTS, DEFAULT_SYSTEM_PROMPT, MAX_RESULTS_PRESETS
from demo.tools import build_tools

load_env()

app = FastAPI(title="Web Router x AI SDK demo")
STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

router = WebRouter()

# In-memory session storage for harness overrides (per-process only)
# Key: session_id (client-generated UUID)
_session_prompts: dict[str, str | None] = {}  # Value: custom prompt or None (cleared)
_session_max_results: dict[str, int] = {}  # Value: 5, 8, or 10 (host preset)


class ChatTurn(BaseModel):
    role: str  # "user" | "assistant" | "system"
    content: str


class ChatRequest(BaseModel):
    """Prefer `messages` (full history). `message` alone is a cold single turn."""

    message: str = ""
    messages: list[ChatTurn] = Field(default_factory=list)
    provider: str = "auto"
    session_id: str = Field(default="")  # Client-generated session UUID
    max_results: int | None = None  # Optional host preset override


class SessionKeysRequest(BaseModel):
    """BYOK paste — empty fields ignored; does not clear host-injected keys."""

    NIMBLE_API_KEY: str = Field(default="")
    TAVILY_API_KEY: str = Field(default="")
    EXA_API_KEY: str = Field(default="")
    OPENAI_API_KEY: str = Field(default="")


class SystemPromptRequest(BaseModel):
    """Set or clear the system prompt for a demo session."""

    session_id: str
    prompt: str | None = None  # None = cleared (no system prompt)


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


@app.get("/api/system-prompt")
def get_system_prompt(session_id: str = "") -> dict:
    """Get the effective system prompt for a session.
    
    Returns the current prompt text, whether it's the default, custom, or cleared,
    and the default prompt text for reference.
    """
    effective = _get_effective_system_prompt(session_id)
    is_default = session_id not in _session_prompts
    is_custom = session_id in _session_prompts and _session_prompts[session_id] is not None
    is_cleared = session_id in _session_prompts and _session_prompts[session_id] is None
    
    return {
        "effective_prompt": effective,
        "default_prompt": DEFAULT_SYSTEM_PROMPT,
        "is_default": is_default,
        "is_custom": is_custom,
        "is_cleared": is_cleared,
    }


@app.post("/api/system-prompt")
def set_system_prompt(req: SystemPromptRequest) -> dict:
    """Set a custom system prompt for a demo session.
    
    Pass prompt as a non-empty string to set custom, or None/"" to clear.
    This is in-memory only (per-process, not written to disk).
    """
    if not req.session_id:
        return {"ok": False, "error": "session_id is required"}
    
    prompt_value = (req.prompt or "").strip() if req.prompt else None
    _session_prompts[req.session_id] = prompt_value
    
    return {
        "ok": True,
        "session_id": req.session_id,
        "is_custom": prompt_value is not None and len(prompt_value) > 0,
        "is_cleared": prompt_value is None,
    }


@app.post("/api/system-prompt/reset")
def reset_system_prompt(session_id: str) -> dict:
    """Reset system prompt to default for a session by removing the override."""
    if session_id and session_id in _session_prompts:
        del _session_prompts[session_id]
    return {"ok": True, "is_default": True}


@app.get("/api/harness")
def get_harness(session_id: str = "") -> dict:
    """Get current harness settings for a session (system prompt + max_results)."""
    system_prompt_info = get_system_prompt(session_id)
    
    max_results = DEFAULT_MAX_RESULTS
    if session_id and session_id in _session_max_results:
        max_results = _session_max_results[session_id]
    
    return {
        **system_prompt_info,
        "max_results": max_results,
        "max_results_default": DEFAULT_MAX_RESULTS,
        "max_results_presets": MAX_RESULTS_PRESETS,
    }


class HarnessRequest(BaseModel):
    """Update harness settings for a session."""

    session_id: str
    prompt: str | None = None  # None = leave unchanged
    max_results: int | None = None  # None = leave unchanged


@app.post("/api/harness")
def update_harness(req: HarnessRequest) -> dict:
    """Update harness settings (system prompt and/or max_results) for a session."""
    if not req.session_id:
        return {"ok": False, "error": "session_id is required"}
    
    result = {"ok": True, "session_id": req.session_id}
    
    # Update system prompt if provided
    if req.prompt is not None:
        prompt_value = req.prompt.strip() if req.prompt else None
        _session_prompts[req.session_id] = prompt_value
        result["is_custom"] = prompt_value is not None and len(prompt_value) > 0
        result["is_cleared"] = prompt_value is None
    
    # Update max_results if provided and valid
    if req.max_results is not None:
        if req.max_results in MAX_RESULTS_PRESETS:
            _session_max_results[req.session_id] = req.max_results
            result["max_results"] = req.max_results
        else:
            result["warning"] = f"max_results must be one of {MAX_RESULTS_PRESETS}"
    
    return result


@app.post("/api/harness/reset")
def reset_harness(session_id: str) -> dict:
    """Reset all harness settings to defaults for a session."""
    if session_id:
        if session_id in _session_prompts:
            del _session_prompts[session_id]
        if session_id in _session_max_results:
            del _session_max_results[session_id]
    return {"ok": True, "is_default": True}


def sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def _get_effective_system_prompt(session_id: str) -> str | None:
    """Return effective system prompt for a session.
    
    Returns:
        - Custom prompt if set for this session
        - None if explicitly cleared for this session
        - DEFAULT_SYSTEM_PROMPT if no override exists
    """
    if not session_id or session_id not in _session_prompts:
        return DEFAULT_SYSTEM_PROMPT
    return _session_prompts[session_id]


def build_messages(req: ChatRequest) -> list:
    """Build ai messages from full history, or fall back to a single user turn."""
    out: list = []
    
    # Add system message if one is configured (default, custom, or cleared)
    system_prompt = _get_effective_system_prompt(req.session_id)
    if system_prompt:
        out.append(ai.system_message(system_prompt))
    
    if req.messages:
        for turn in req.messages:
            role = (turn.role or "").lower().strip()
            content = (turn.content or "").strip()
            if not content:
                continue
            if role == "assistant":
                out.append(ai.assistant_message(content))
            elif role == "system":
                # Ignore client system turns; host owns system prompt via harness API.
                continue
            else:
                out.append(ai.user_message(content))
        return out
    if req.message.strip():
        out.append(ai.user_message(req.message.strip()))
        return out
    return out


async def stream_agent_turn(req: ChatRequest) -> AsyncIterator[str]:
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

    messages = build_messages(req)
    if len(messages) < 1:
        yield sse("error", {"message": "Send a non-empty message (or messages history)."})
        return

    # Use max_results from request, session storage, or default
    max_results = req.max_results
    if max_results is None and req.session_id and req.session_id in _session_max_results:
        max_results = _session_max_results[req.session_id]
    if max_results is None:
        max_results = DEFAULT_MAX_RESULTS

    tools = build_tools(router, provider=req.provider, max_results=max_results)
    agent = ai.Agent(tools=tools)
    model = ai.get_model("openai:gpt-4o-mini")

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
        stream_agent_turn(req),
        media_type="text/event-stream",
    )
