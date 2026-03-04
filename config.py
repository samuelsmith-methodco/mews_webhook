"""Configuration for Mews webhook receiver.

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


def _env(name: str, default: Optional[str] = None) -> Optional[str]:
    return os.environ.get(name, default)


# Optional: shared secret Mews adds to the webhook URL. Leave unset during certification.
WEBHOOK_TOKEN: Optional[str] = _env("MEWS_WEBHOOK_TOKEN")

# WebSocket (optional): set only after certification when Mews gives you these tokens.
MEWS_WS_BASE_URL: Optional[str] = _env("MEWS_WS_BASE_URL")
MEWS_CLIENT_TOKEN: Optional[str] = _env("MEWS_CLIENT_TOKEN")
MEWS_ACCESS_TOKEN: Optional[str] = _env("MEWS_ACCESS_TOKEN")

# Bind host/port for Uvicorn
HOST: str = _env("HOST", "0.0.0.0") or "0.0.0.0"
PORT: int = int(_env("PORT", "8000") or "8000")
