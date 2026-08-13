"""SlimmeLezer Démász custom integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import PLATFORMS
from .coordinator import SlimmeLezerCoordinator
from .reporting import UnknownObisReporter


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up SlimmeLezer Démász from a config entry."""
    coordinator = SlimmeLezerCoordinator(hass, entry)
    reporter = UnknownObisReporter(hass, entry)
    await reporter.async_initialize()
    coordinator.reporter = reporter
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
