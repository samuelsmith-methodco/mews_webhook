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
| `MEWS_WS_BASE_URL` | No | Optional | Mews WebSocket base URL. **Defaults to `wss://ws.mews.com`** (production). Override for Demo. |
| `MEWS_CLIENT_TOKEN` or `MEWS_ClientToken` | No | **After certification** | Client token — provided by Mews. Either spelling is accepted. |
| `MEWS_ACCESS_TOKEN` or `MEWS_AccessToken` | No | **After certification** | Per-enterprise token — from the enterprise admin. Either spelling is accepted. |
| `HOST` | No | Optional | Bind host (default `0.0.0.0`). |
| `PORT` | No | Optional | Bind port (default `8000`). |

**Loading .env:** The app loads a `.env` file from the current working directory (via `python-dotenv`). For **Railway** (and similar PaaS), the app does **not** read a `.env` file at runtime — add `MEWS_ClientToken` and `MEWS_AccessToken` in the service **Variables** tab in the Railway dashboard so they are injected as environment variables.

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
- **WS /ws/events** – Inbound WebSocket for testing. Send Mews-style JSON: `{"Events": [{"Type": "...", ...}, ...]}`. Server replies with `{"ok": true, "processed": N}` or an error. Use from Postman (New → WebSocket) or a script to test Command, Reservation, Resource, and PriceUpdate without Mews credentials.

## Webhook authentication

If you register a shared secret with Mews, set `MEWS_WEBHOOK_TOKEN`. Mews may send the token as a query parameter; the server also accepts `X-Webhook-Token` header.

## WebSocket

### Outbound client (Mews)

If `MEWS_WS_BASE_URL`, `MEWS_CLIENT_TOKEN`, and `MEWS_ACCESS_TOKEN` are set, the app opens a background WebSocket connection to `{MEWS_WS_BASE_URL}/ws/connector` with exponential backoff on reconnect, and processes Command, Reservation, Resource, and PriceUpdate events. Events are logged; extend `handlers.process_websocket_events` for your logic.

### Testing WebSocket events (inbound `/ws/events`)

Connect to `ws://127.0.0.1:8000/ws/events` (e.g. in Postman: New → WebSocket, enter the URL, Connect). Send a JSON message in Mews format:

```json
{
  "Events": [
    { "Type": "DeviceCommand", "Id": "2391a3df-1c61-4131-b6f8-c85b4234adcb", "State": "Pending" },
    { "Type": "Reservation", "Id": "bfee2c44-1f84-4326-a862-5289598f6e2d", "State": "Processed", "StartUtc": "2016-02-20T13:00:00Z", "EndUtc": "2016-02-22T11:00:00Z" },
    { "Type": "Resource", "Id": "5ee074b1-6c86-48e8-915f-c7aa4702086f", "State": "Dirty" },
    { "Type": "PriceUpdate", "Id": "bd75f159-f22a-4685-abdb-aac0008e2af3", "StartUtc": "2019-09-07T22:00:00Z", "EndUtc": "2019-09-07T22:00:00Z", "RateId": "9c6c0556-42bb-409a-86ca-6ca430773b99", "ResourceCategoryId": null }
  ]
}
```

The server processes the events (same handler as Mews WebSocket) and replies with `{"ok": true, "processed": 4}`. Check the server console for log lines for each event type.

## Next steps

- In `handlers.py`: call Mews API (e.g. **Get all reservations**, **Get all resources**) using the event IDs, then implement your business logic.
- Register your webhook URL with Mews (e.g. `https://your-domain/webhook/general`) and optional token via Mews support.
