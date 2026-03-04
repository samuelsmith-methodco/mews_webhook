"""Async handlers for General Webhook and WebSocket events."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from schemas import (
    GENERAL_WEBHOOK_EVENT_DISCRIMINATORS,
    GeneralWebhookPayload,
    RESOURCE_UPDATED,
    SERVICE_ORDER_UPDATED,
)

logger = logging.getLogger(__name__)


async def process_general_webhook(payload: GeneralWebhookPayload) -> None:
    """
    Process a General Webhook payload asynchronously.
    Called after responding 202 to Mews so the request does not time out.
    """
    enterprise_id = payload.EnterpriseId
    integration_id = payload.IntegrationId
    for ev in payload.Events:
        disc = ev.Discriminator
        entity_id = ev.Value.Id
        if disc == SERVICE_ORDER_UPDATED:
            await on_reservation_event(
                enterprise_id=enterprise_id,
                integration_id=integration_id,
                reservation_id=entity_id,
            )
        elif disc == RESOURCE_UPDATED:
            await on_resource_event(
                enterprise_id=enterprise_id,
                integration_id=integration_id,
                resource_id=entity_id,
            )
        elif disc in GENERAL_WEBHOOK_EVENT_DISCRIMINATORS:
            logger.info(
                "General webhook event (other): discriminator=%s enterprise=%s integration=%s id=%s",
                disc,
                enterprise_id,
                integration_id,
                entity_id,
            )
        else:
            logger.warning("Unknown General Webhook discriminator: %s", disc)


async def on_reservation_event(
    *,
    enterprise_id: str,
    integration_id: str,
    reservation_id: str,
) -> None:
    """Handle Reservation (ServiceOrder) updated from General Webhook."""
    logger.info(
        "Reservation event: enterprise=%s integration=%s reservation_id=%s",
        enterprise_id,
        integration_id,
        reservation_id,
    )
    # TODO: call Mews API Get all reservations with reservation_id, then your business logic
    await asyncio.sleep(0)


async def on_resource_event(
    *,
    enterprise_id: str,
    integration_id: str,
    resource_id: str,
) -> None:
    """Handle Resource updated from General Webhook."""
    logger.info(
        "Resource event: enterprise=%s integration=%s resource_id=%s",
        enterprise_id,
        integration_id,
        resource_id,
    )
    # TODO: call Mews API Get all resources with resource_id, then your business logic
    await asyncio.sleep(0)


def process_websocket_events(events: list[dict[str, Any]]) -> None:
    """
    Process events received from Mews WebSocket (Command, Reservation, Resource, PriceUpdate).
    Run in the WebSocket client loop; keep lightweight or offload to queue.
    """
    for ev in events:
        typ = ev.get("Type")
        if typ == "DeviceCommand":
            logger.info("WebSocket DeviceCommand: id=%s state=%s", ev.get("Id"), ev.get("State"))
        elif typ == "Reservation":
            logger.info(
                "WebSocket Reservation: id=%s state=%s start=%s end=%s",
                ev.get("Id"),
                ev.get("State"),
                ev.get("StartUtc"),
                ev.get("EndUtc"),
            )
        elif typ == "Resource":
            logger.info("WebSocket Resource: id=%s state=%s", ev.get("Id"), ev.get("State"))
        elif typ == "PriceUpdate":
            logger.info(
                "WebSocket PriceUpdate: id=%s rate=%s start=%s end=%s",
                ev.get("Id"),
                ev.get("RateId"),
                ev.get("StartUtc"),
                ev.get("EndUtc"),
            )
        else:
            logger.warning("Unknown WebSocket event type: %s", typ)
