"""Polling coordinator for the SlimmeLezer Démász integration."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from aiohttp import ClientError
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_RESOURCE_URL,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TIMEOUT,
    DOMAIN,
    update_interval,
)
from .parser import TelegramData, TelegramParseError, parse_telegram

if TYPE_CHECKING:
    from .reporting import UnknownObisReporter

LOGGER = logging.getLogger(__name__)


async def async_fetch_telegram(hass: HomeAssistant, resource_url: str) -> TelegramData:
    """Fetch and parse one raw telegram from ESPHome's web server."""
    session = async_get_clientsession(hass)
    try:
        async with asyncio.timeout(DEFAULT_TIMEOUT):
            response = await session.get(resource_url)
            response.raise_for_status()
            payload = await response.json(content_type=None)
    except (TimeoutError, ClientError, ValueError) as err:
        raise UpdateFailed(f"A Raw DSMR Telegram nem olvasható: {err}") from err

    telegram = payload.get("value") if isinstance(payload, dict) else None
    if not isinstance(telegram, str):
        raise UpdateFailed("A JSON-válasz nem tartalmaz szöveges 'value' mezőt.")
    try:
        return parse_telegram(telegram)
    except TelegramParseError as err:
        raise UpdateFailed(str(err)) from err


class SlimmeLezerCoordinator(DataUpdateCoordinator[TelegramData]):
    """Coordinate one HTTP request for every SlimmeLezer entity update."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self.resource_url: str = entry.data[CONF_RESOURCE_URL]
        self.reporter: UnknownObisReporter | None = None
        seconds = int(entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))
        super().__init__(
            hass,
            LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=update_interval(seconds),
        )

    async def _async_update_data(self) -> TelegramData:
        """Fetch one coordinated data snapshot."""
        return await async_fetch_telegram(self.hass, self.resource_url)
