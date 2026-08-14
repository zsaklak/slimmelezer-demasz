"""Privacy-safe diagnostics for SlimmeLezer Démász."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_POWER_EXPORT_ENTITY, CONF_POWER_IMPORT_ENTITY
from .coordinator import SlimmeLezerCoordinator


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics without telegram values or meter identifiers."""
    coordinator: SlimmeLezerCoordinator = entry.runtime_data
    data = coordinator.data
    return {
        "update_success": coordinator.last_update_success,
        "using_stale_data": coordinator.using_stale_data,
        "consecutive_failed_refreshes": coordinator.consecutive_failed_refreshes,
        "total_failed_refreshes": coordinator.total_failed_refreshes,
        "stale_refreshes": coordinator.stale_refreshes,
        "last_failure_stage": coordinator.last_failure_stage,
        "last_failure_type": coordinator.last_failure_type,
        "telegram_header": data.header,
        "telegram_length": data.telegram_length,
        "observed_obis_count": len(data.obis_codes),
        "observed_obis_codes": sorted(data.obis_codes),
        "created_sensor_count": len(data.registers),
        "unknown_obis_codes": sorted(data.unknown_codes),
        "github_reporting": (
            coordinator.reporter.mode if coordinator.reporter is not None else "manual"
        ),
        "github_reported_fingerprints": (
            coordinator.reporter.reported_count
            if coordinator.reporter is not None
            else 0
        ),
        "selected_power_sources_configured": bool(
            entry.options.get(CONF_POWER_IMPORT_ENTITY)
            and entry.options.get(CONF_POWER_EXPORT_ENTITY)
        ),
    }
