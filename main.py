"""
Mews webhook receiver: FastAPI + Uvicorn.

- General Webhook: POST /webhook/general (Reservation + Resource events).
- Optional WebSocket client to Mews for Command, Reservation, Resource, PriceUpdate.
"""
from __future__ import annotations

import asyncio
import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
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
    """Connect to Mews WebSocket and process Command, Reservation, Resource, PriceUpdate events."""
    try:
        import websockets
    except ImportError:
        logger.warning("websockets not installed; Mews WebSocket client disabled. pip install websockets")
        return
    base = (config.MEWS_WS_BASE_URL or "").rstrip("/")
    client_token = config.MEWS_CLIENT_TOKEN
    access_token = config.MEWS_ACCESS_TOKEN
    if not base or not client_token or not access_token:
        logger.info("Mews WebSocket not configured (MEWS_WS_BASE_URL, MEWS_CLIENT_TOKEN, MEWS_ACCESS_TOKEN); skipping.")
        return
    url = f"{base}/ws/connector"
    # Cookie: ClientToken=...; AccessToken=... (no spaces around =)
    cookies = f"ClientToken={client_token};AccessToken={access_token}"
    headers = {"Cookie": cookies}
    while True:
        try:
            async with websockets.connect(url, extra_headers=headers) as ws:
                logger.info("Connected to Mews WebSocket %s", url)
                async for raw in ws:
                    try:
                        import json
                        data = json.loads(raw)
                        events = data.get("Events") or []
                        process_websocket_events(events)
                    except Exception as e:
                        logger.exception("WebSocket message handling error: %s", e)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.exception("Mews WebSocket connection error: %s", e)
        await asyncio.sleep(5)


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
