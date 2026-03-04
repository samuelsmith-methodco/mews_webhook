"""Pydantic models for Mews General Webhook and WebSocket events."""
from __future__ import annotations

from typing import Any, Literal, Union

from pydantic import BaseModel, Field


# ----- General Webhook (HTTP POST) -----

class EntityUpdatedValue(BaseModel):
    """Value for events that carry only entity Id (fetch via API)."""
    Id: str


class GeneralWebhookEvent(BaseModel):
    """Single event in General Webhook payload."""
    Discriminator: str  # ServiceOrderUpdated | ResourceUpdated | MessageAdded | ...
    Value: EntityUpdatedValue


class GeneralWebhookPayload(BaseModel):
    """Body of General Webhook POST from Mews."""
    EnterpriseId: str
    IntegrationId: str
    Events: list[GeneralWebhookEvent] = Field(default_factory=list)


# Discriminators we care about (per your subscription: Reservation + Resource)
SERVICE_ORDER_UPDATED = "ServiceOrderUpdated"  # Reservations
RESOURCE_UPDATED = "ResourceUpdated"

# All known General Webhook discriminators (for logging others)
GENERAL_WEBHOOK_EVENT_DISCRIMINATORS = frozenset({
    "ServiceOrderUpdated",
    "ResourceUpdated",
    "MessageAdded",
    "ResourceBlockUpdated",
    "CustomerAdded",
    "CustomerUpdated",
    "PaymentUpdated",
})


# ----- WebSocket events (we receive from Mews WS) -----

class DeviceCommandEvent(BaseModel):
    Type: Literal["DeviceCommand"]
    Id: str
    State: str


class ReservationWsEvent(BaseModel):
    Type: Literal["Reservation"]
    Id: str
    State: str
    StartUtc: str
    EndUtc: str
    AssignedResourceId: str | None = None


class ResourceWsEvent(BaseModel):
    Type: Literal["Resource"]
    Id: str
    State: str


class PriceUpdateWsEvent(BaseModel):
    Type: Literal["PriceUpdate"]
    Id: str
    StartUtc: str | None = None
    EndUtc: str | None = None
    RateId: str | None = None
    ResourceCategoryId: str | None = None


WsEvent = Union[DeviceCommandEvent, ReservationWsEvent, ResourceWsEvent, PriceUpdateWsEvent]


class WebSocketMessage(BaseModel):
    """Message body received over Mews WebSocket."""
    Events: list[dict[str, Any]]  # parsed per event Type
