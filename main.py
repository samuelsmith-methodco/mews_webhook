"""
Mews webhook receiver: FastAPI + Uvicorn.

- General Webhook: POST /webhook/general (Reservation + Resource events).
- WebSocket client to Mews for Command, Reservation, Resource, PriceUpdate (when configured).
- Inbound WebSocket /ws/events for testing (same message format as Mews).
"""
from __future__ import annotations

import asyncio
import json
import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, status
from fastapi.responses import JSONResponse

import config
from handlers import process_general_webhook, process_websocket_events
from schemas import GeneralWebhookPayload

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


async def run_mews_websocket_client() -> None:
    """Connect to Mews WebSocket and process Command, Reservation, Resource, PriceUpdate events.
    Keeps connection alive with frequent pings and reconnects on any disconnect.
    """
    try:
        import websockets
    except ImportError:
        logger.warning("websockets not installed; Mews WebSocket client disabled. pip install websockets")
        return
    base = (config.MEWS_WS_BASE_URL or "").rstrip("/")
    client_token = config.MEWS_CLIENT_TOKEN
    access_token = config.MEWS_ACCESS_TOKEN
    if not base or not client_token or not access_token:
        logger.info(
            "Mews WebSocket not configured: set MEWS_ClientToken (or MEWS_CLIENT_TOKEN) and "
            "MEWS_AccessToken (or MEWS_ACCESS_TOKEN); optionally MEWS_WS_BASE_URL (default wss://ws.mews.com). Skipping."
        )
        return
    url = f"{base}/ws/connector"
    cookies = f"ClientToken={client_token};AccessToken={access_token}"
    headers = {"Cookie": cookies}
    backoff_sec = 5
    max_backoff_sec = 300
    keepalive_interval_sec = 15
    while True:
        try:
            async with websockets.connect(
                url,
                extra_headers=headers,
                ping_interval=keepalive_interval_sec,
                ping_timeout=10,
                close_timeout=5,
            ) as ws:
                backoff_sec = 5
                logger.info("Connected to Mews WebSocket %s (keepalive every %ss)", url, keepalive_interval_sec)
                async for raw in ws:
                    try:
                        data = json.loads(raw)
                        events = data.get("Events") or []
                        process_websocket_events(events)
                    except Exception as e:
                        logger.exception("WebSocket message handling error: %s", e)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.exception("Mews WebSocket connection error: %s", e)
        delay = min(backoff_sec, max_backoff_sec)
        logger.info("Mews WebSocket disconnected; reconnecting in %s seconds", delay)
        await asyncio.sleep(delay)
        backoff_sec = min(backoff_sec * 2, max_backoff_sec)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start background WebSocket client if configured."""
    task = asyncio.create_task(run_mews_websocket_client())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="Mews Webhook Receiver",
    description="Receives Mews General Webhooks (Reservation, Resource) and optional WebSocket events.",
    lifespan=lifespan,
)


@app.get("/")
async def root():
    return {"service": "mews-webhook", "status": "ok"}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.websocket("/ws/events")
async def websocket_events(websocket: WebSocket):
    """
    Inbound WebSocket for testing Mews-style events (Command, Reservation, Resource, PriceUpdate).
    Send JSON messages: {"Events": [{"Type": "...", ...}, ...]}.
    Same format as Mews WebSocket; use from Postman or a script to test without Mews credentials.
    """
    await websocket.accept()
    logger.info("WebSocket client connected to /ws/events")
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
                events = data.get("Events") or []
                process_websocket_events(events)
                await websocket.send_json({"ok": True, "processed": len(events)})
            except json.JSONDecodeError as e:
                await websocket.send_json({"ok": False, "error": f"Invalid JSON: {e}"})
            except Exception as e:
                logger.exception("WebSocket event handling error: %s", e)
                await websocket.send_json({"ok": False, "error": str(e)})
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected from /ws/events")


def _check_webhook_token(request: Request) -> bool:
    """Return True if no token configured or request carries the configured token."""
    if not config.WEBHOOK_TOKEN:
        return True
    # Mews can add token to URL: https://your-server/webhook/general?token=SECRET
    token = request.query_params.get("token")
    if token and token == config.WEBHOOK_TOKEN:
        return True
    # Or e.g. header X-Webhook-Token (if you agree with Mews)
    auth = request.headers.get("X-Webhook-Token")
    if auth and auth == config.WEBHOOK_TOKEN:
        return True
    return False


@app.post("/webhook/general", status_code=status.HTTP_202_ACCEPTED)
async def general_webhook(request: Request, payload: GeneralWebhookPayload):
    """
    Receive Mews General Webhook (Reservation + Resource events).
    Responds immediately with 202 Accepted and processes events asynchronously.
    """
    if not _check_webhook_token(request):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Invalid or missing webhook token"},
        )
    asyncio.create_task(process_general_webhook(payload))
    return {"received": True, "events_count": len(payload.Events)}


def run() -> None:
    import uvicorn
    uvicorn.run(
        "main:app",
        host=config.HOST,
        port=config.PORT,
        reload=False,
    )


if __name__ == "__main__":
    run()
