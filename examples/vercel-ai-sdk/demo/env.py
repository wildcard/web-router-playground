"""Load API keys for the demo.

Keys come from a local `.env` at the repo root (gitignored). Never print them.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

LOCAL_ENV = Path(__file__).resolve().parents[1] / ".env"


def load_env() -> None:
    """Load env vars from the repo-local `.env` if present."""
    if LOCAL_ENV.exists():
        load_dotenv(LOCAL_ENV, override=False)


def configured_providers() -> dict[str, bool]:
    return {
        "nimble": bool(os.environ.get("NIMBLE_API_KEY")),
        "tavily": bool(os.environ.get("TAVILY_API_KEY")),
        "exa": bool(os.environ.get("EXA_API_KEY")),
    }


def has_openai_key() -> bool:
    return bool(os.environ.get("OPENAI_API_KEY"))
