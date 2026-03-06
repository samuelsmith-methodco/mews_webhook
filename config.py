"""Configuration for Mews webhook receiver.

Loads .env from the current working directory so MEWS_ClientToken, MEWS_AccessToken, etc.
can be set in a .env file. On Railway/Heroku, set variables in the dashboard (no .env at runtime).

Env vars:
  None required. For certification you can run with no env vars.

  Optional (webhook):
    MEWS_WEBHOOK_TOKEN - Shared secret for webhook URL (Mews may add ?token=...).
                         Set only after Mews gives you a token to register.

  Optional (WebSocket; only after certification when Mews provides tokens):
    MEWS_WS_BASE_URL   - e.g. wss://ws.mews.com (Demo/Production address from Mews).
    MEWS_CLIENT_TOKEN  - Provided by Mews upon successful certification.
    MEWS_ACCESS_TOKEN  - Per-enterprise; from the enterprise admin in Mews.

  Optional (server):
    HOST, PORT - Bind address (default 0.0.0.0:8000).
"""
from __future__ import annotations

import os
from typing import Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # no .env loading without python-dotenv


def _env(name: str, default: Optional[str] = None) -> Optional[str]:
    return os.environ.get(name, default)


# Optional: shared secret Mews adds to the webhook URL. Leave unset during certification.
WEBHOOK_TOKEN: Optional[str] = _env("MEWS_WEBHOOK_TOKEN")

# WebSocket: accept either MEWS_CLIENT_TOKEN or MEWS_ClientToken (same for Access).
# MEWS_WS_BASE_URL defaults to production; override for Demo.
MEWS_WS_BASE_URL: Optional[str] = _env("MEWS_WS_BASE_URL") or "wss://ws.mews.com"
MEWS_CLIENT_TOKEN: Optional[str] = _env("MEWS_CLIENT_TOKEN") or _env("MEWS_ClientToken")
MEWS_ACCESS_TOKEN: Optional[str] = _env("MEWS_ACCESS_TOKEN") or _env("MEWS_AccessToken")

# Bind host/port for Uvicorn
HOST: str = _env("HOST", "0.0.0.0") or "0.0.0.0"
PORT: int = int(_env("PORT", "8000") or "8000")
