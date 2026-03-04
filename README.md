# Mews Webhook Receiver

FastAPI + Uvicorn server that receives **Mews General Webhooks** (Reservation + Resource) and optionally connects to **Mews WebSockets** for Command, Reservation, Resource, and Price update events.

## Subscribed events

- **General Webhook (HTTP POST):** Reservation (ServiceOrderUpdated), Resource (ResourceUpdated).
- **WebSocket (client to Mews):** Command (DeviceCommand), Reservation, Resource, PriceUpdate.

## Setup

```bash
cd mews_webhook
pip install -r requirements.txt
```

## Environment variables

**None are required.** You can run the server with no env vars for certification.

| Variable | Required? | When to set | Description |
|----------|-----------|-------------|-------------|
| `MEWS_WEBHOOK_TOKEN` | No | After Mews gives you a secret | Shared secret for webhook URL (query `?token=...` or header `X-Webhook-Token`). Omit during certification if no token is used. |
| `MEWS_WS_BASE_URL` | No | **After certification** | Mews WebSocket base URL (e.g. `wss://ws.mews.com`). |
| `MEWS_CLIENT_TOKEN` | No | **After certification** | Client token — **provided by Mews upon successful certification**. |
| `MEWS_ACCESS_TOKEN` | No | **After certification** | Per-enterprise token — from the enterprise admin in Mews. |
| `HOST` | No | Optional | Bind host (default `0.0.0.0`). |
| `PORT` | No | Optional | Bind port (default `8000`). |

### During certification

- You **do not** have `MEWS_CLIENT_TOKEN` or `MEWS_ACCESS_TOKEN` yet; Mews provides those after certification. Leave `MEWS_WS_BASE_URL`, `MEWS_CLIENT_TOKEN`, and `MEWS_ACCESS_TOKEN` **unset**. The app will only run the **General Webhook** endpoint; the WebSocket client will stay disabled and log that it is not configured.
- You only need the server running and a **public URL** for **POST /webhook/general** (e.g. via ngrok or your deployed host). Give that URL to Mews when they ask for your webhook endpoint.
- If Mews asks you to use a shared secret in the webhook URL, they will give you a token — then set `MEWS_WEBHOOK_TOKEN` to that value.

## Run

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

Or:

```bash
python main.py
```

## Endpoints

- **GET /** – Service info.
- **GET /health** – Health check.
- **POST /webhook/general** – Mews General Webhook. Expects JSON body with `EnterpriseId`, `IntegrationId`, `Events[]`. Responds with **202 Accepted** and processes events asynchronously (respond within 5 seconds as per Mews FAQ).

## Webhook authentication

If you register a shared secret with Mews, set `MEWS_WEBHOOK_TOKEN`. Mews may send the token as a query parameter; the server also accepts `X-Webhook-Token` header.

## WebSocket client

If `MEWS_WS_BASE_URL`, `MEWS_CLIENT_TOKEN`, and `MEWS_ACCESS_TOKEN` are set, the app opens a background WebSocket connection to `{MEWS_WS_BASE_URL}/ws/connector` and processes Command, Reservation, Resource, and PriceUpdate events. Events are logged; extend `handlers.process_websocket_events` for your logic.

## Next steps

- In `handlers.py`: call Mews API (e.g. **Get all reservations**, **Get all resources**) using the event IDs, then implement your business logic.
- Register your webhook URL with Mews (e.g. `https://your-domain/webhook/general`) and optional token via Mews support.
