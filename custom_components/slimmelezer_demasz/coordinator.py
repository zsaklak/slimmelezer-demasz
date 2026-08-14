"""Polling coordinator for the SlimmeLezer Démász integration."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from aiohttp import ClientError, ClientResponseError
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
    FETCH_ATTEMPTS,
    FETCH_RETRY_DELAY,
    STALE_DATA_GRACE_REFRESHES,
    update_interval,
)
from .parser import TelegramData, TelegramParseError, parse_telegram

if TYPE_CHECKING:
    from .reporting import UnknownObisReporter

LOGGER = logging.getLogger(__name__)


class TelegramFetchError(UpdateFailed):
    """Describe a privacy-safe raw telegram fetch failure."""

    def __init__(self, stage: str, error_type: str, message: str) -> None:
        super().__init__(message)
        self.stage = stage
        self.error_type = error_type


async def _async_fetch_telegram_once(
    hass: HomeAssistant, resource_url: str
) -> TelegramData:
    """Fetch and parse one raw telegram without retrying."""
    session = async_get_clientsession(hass)
    try:
        async with asyncio.timeout(DEFAULT_TIMEOUT):
            response = await session.get(resource_url)
            response.raise_for_status()
            payload = await response.json(content_type=None)
    except TimeoutError as err:
        raise TelegramFetchError(
            "http_timeout",
            type(err).__name__,
            f"A Raw DSMR Telegram lekérése {DEFAULT_TIMEOUT} másodperc után "
            "időtúllépéssel leállt.",
        ) from err
    except ClientError as err:
        status = f", HTTP {err.status}" if isinstance(err, ClientResponseError) else ""
        raise TelegramFetchError(
            "http",
            type(err).__name__,
            f"A Raw DSMR Telegram HTTP-lekérése sikertelen "
            f"({type(err).__name__}{status}).",
        ) from err
    except ValueError as err:
        raise TelegramFetchError(
            "json",
            type(err).__name__,
            f"A Raw DSMR Telegram végpontja nem érvényes JSON-választ adott "
            f"({type(err).__name__}).",
        ) from err

    telegram = payload.get("value") if isinstance(payload, dict) else None
    if not isinstance(telegram, str):
        raise TelegramFetchError(
            "payload",
            "MissingTextValue",
            "A JSON-válasz nem tartalmaz szöveges 'value' mezőt.",
        )
    try:
        return parse_telegram(telegram)
    except TelegramParseError as err:
        raise TelegramFetchError(
            "telegram",
            type(err).__name__,
            str(err),
        ) from err


async def async_fetch_telegram(hass: HomeAssistant, resource_url: str) -> TelegramData:
    """Fetch a raw telegram, retrying one transient failure."""
    for attempt in range(1, FETCH_ATTEMPTS + 1):
        try:
            return await _async_fetch_telegram_once(hass, resource_url)
        except TelegramFetchError as err:
            if attempt >= FETCH_ATTEMPTS:
                raise
            LOGGER.warning(
                "Raw DSMR lekérési kísérlet sikertelen "
                "(fázis=%s, típus=%s, kísérlet=%d/%d); újrapróbálkozás %.2f "
                "másodperc múlva",
                err.stage,
                err.error_type,
                attempt,
                FETCH_ATTEMPTS,
                FETCH_RETRY_DELAY,
            )
            await asyncio.sleep(FETCH_RETRY_DELAY)

    raise RuntimeError("A Raw DSMR újrapróbálkozási ciklus váratlanul véget ért.")


class SlimmeLezerCoordinator(DataUpdateCoordinator[TelegramData]):
    """Coordinate one HTTP request for every SlimmeLezer entity update."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self.resource_url: str = entry.data[CONF_RESOURCE_URL]
        self.reporter: UnknownObisReporter | None = None
        self.consecutive_failed_refreshes = 0
        self.total_failed_refreshes = 0
        self.stale_refreshes = 0
        self.using_stale_data = False
        self.last_failure_stage: str | None = None
        self.last_failure_type: str | None = None
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
        try:
            data = await async_fetch_telegram(self.hass, self.resource_url)
        except TelegramFetchError as err:
            self.consecutive_failed_refreshes += 1
            self.total_failed_refreshes += 1
            self.last_failure_stage = err.stage
            self.last_failure_type = err.error_type
            if (
                self.data is not None
                and self.consecutive_failed_refreshes <= STALE_DATA_GRACE_REFRESHES
            ):
                self.using_stale_data = True
                self.stale_refreshes += 1
                LOGGER.warning(
                    "Raw DSMR frissítés sikertelen "
                    "(fázis=%s, típus=%s, egymást követő hiba=%d/%d); "
                    "az utolsó jó adat elérhető marad",
                    err.stage,
                    err.error_type,
                    self.consecutive_failed_refreshes,
                    STALE_DATA_GRACE_REFRESHES,
                )
                return self.data
            self.using_stale_data = False
            raise

        if self.consecutive_failed_refreshes:
            LOGGER.info(
                "A Raw DSMR frissítés helyreállt %d egymást követő sikertelen "
                "frissítés után",
                self.consecutive_failed_refreshes,
            )
        self.consecutive_failed_refreshes = 0
        self.using_stale_data = False
        return data
