"""Load API keys for the demo.

Keys come from (in precedence order for a given name):
  1. Process environment already set by the host (Exe invite / Nimble-hosted session)
  2. A local `.env` next to this example (gitignored BYOK) — loaded with override=False

Never print key values. Never commit `.env`.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

LOCAL_ENV = Path(__file__).resolve().parents[1] / ".env"

# Names the session-keys UI / host may set. Values are never logged.
KEY_NAMES = (
    "NIMBLE_API_KEY",
    "TAVILY_API_KEY",
    "EXA_API_KEY",
    "OPENAI_API_KEY",
)


def load_env() -> None:
    """Load env vars from the example-local `.env` if present.

    Uses override=False so host process env (mode b: Nimble-hosted invite) wins
    over a file `.env`.
    """
    if LOCAL_ENV.exists():
        load_dotenv(LOCAL_ENV, override=False)


def apply_session_keys(keys: dict[str, str]) -> dict[str, bool]:
    """Apply partner-pasted keys into process env for this run only.

    Empty strings are ignored (do not wipe host-injected keys). Does not write
    to disk. Returns which known key names are now configured.
    """
    for name in KEY_NAMES:
        value = (keys.get(name) or "").strip()
        if value:
            os.environ[name] = value
    return configured_status()


def configured_providers() -> dict[str, bool]:
    return {
        "nimble": bool(os.environ.get("NIMBLE_API_KEY")),
        "tavily": bool(os.environ.get("TAVILY_API_KEY")),
        "exa": bool(os.environ.get("EXA_API_KEY")),
    }


def has_openai_key() -> bool:
    return bool(os.environ.get("OPENAI_API_KEY"))


def configured_status() -> dict[str, bool]:
    status = configured_providers()
    status["openai"] = has_openai_key()
    return status
