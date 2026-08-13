"""Dynamic sensor platform for SlimmeLezer Démász."""

from __future__ import annotations

import logging
import re
from typing import Any, ClassVar

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, UnitOfPower
from homeassistant.core import Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util.unit_conversion import PowerConverter

from .const import (
    CONF_POWER_EXPORT_ENTITY,
    CONF_POWER_IMPORT_ENTITY,
    DOMAIN,
    MANUFACTURER,
    MODEL,
)
from .coordinator import SlimmeLezerCoordinator
from .parser import RegisterValue

LOGGER = logging.getLogger(__name__)

DEVICE_CLASSES = {
    "energy": SensorDeviceClass.ENERGY,
    "reactive_energy": SensorDeviceClass.REACTIVE_ENERGY,
    "power": SensorDeviceClass.POWER,
    "reactive_power": SensorDeviceClass.REACTIVE_POWER,
    "voltage": SensorDeviceClass.VOLTAGE,
    "current": SensorDeviceClass.CURRENT,
    "frequency": SensorDeviceClass.FREQUENCY,
    "power_factor": SensorDeviceClass.POWER_FACTOR,
    "volume": SensorDeviceClass.VOLUME,
}
STATE_CLASSES = {
    "measurement": SensorStateClass.MEASUREMENT,
    "total": SensorStateClass.TOTAL,
    "total_increasing": SensorStateClass.TOTAL_INCREASING,
}


def _source_key(entry: ConfigEntry) -> str:
    """Return a stable source identifier without exposing the full URL."""
    source = entry.unique_id or entry.entry_id
    return re.sub(r"[^a-z0-9]+", "_", source.lower()).strip("_")


def _device_info(entry: ConfigEntry) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, _source_key(entry))},
        name="SlimmeLezer Démász",
        manufacturer=MANUFACTURER,
        model=MODEL,
        configuration_url=entry.data.get("resource_url"),
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up current sensors and discover future OBIS registers."""
    coordinator: SlimmeLezerCoordinator = entry.runtime_data
    known_keys: set[str] = set()

    @callback
    def async_discover_registers() -> None:
        current_keys = set(coordinator.data.registers)
        new_keys = current_keys - known_keys
        if not new_keys:
            return
        known_keys.update(new_keys)
        entities = [
            SlimmeLezerRegisterSensor(coordinator, entry, key)
            for key in sorted(new_keys)
        ]
        async_add_entities(entities)
        newly_unknown = sorted(
            {
                coordinator.data.registers[key].obis
                for key in new_keys
                if not coordinator.data.registers[key].known
            }
        )
        if newly_unknown:
            LOGGER.warning(
                "Új, automatikusan felvett OBIS-regiszterek: %s",
                ", ".join(newly_unknown),
            )
            if coordinator.reporter is not None:
                entry.async_create_background_task(
                    hass,
                    coordinator.reporter.async_report_codes(
                        coordinator.data, newly_unknown
                    ),
                    f"{DOMAIN} ismeretlen OBIS-jelentés",
                )

    async_discover_registers()
    entry.async_on_unload(coordinator.async_add_listener(async_discover_registers))

    async_add_entities(
        [
            SlimmeLezerGridNetPowerSensor(coordinator, entry),
            SlimmeLezerDiagnosticSensor(coordinator, entry, "obis_count"),
            SlimmeLezerDiagnosticSensor(coordinator, entry, "dynamic_count"),
            SlimmeLezerDiagnosticSensor(coordinator, entry, "unknown_count"),
            SlimmeLezerDiagnosticSensor(coordinator, entry, "telegram_length"),
            SlimmeLezerDiagnosticSensor(coordinator, entry, "reported_count"),
        ]
    )
    import_entity = entry.options.get(CONF_POWER_IMPORT_ENTITY)
    export_entity = entry.options.get(CONF_POWER_EXPORT_ENTITY)
    if import_entity and export_entity:
        async_add_entities(
            [SlimmeLezerSelectedNetPowerSensor(entry, import_entity, export_entity)]
        )


class SlimmeLezerSelectedNetPowerSensor(SensorEntity):
    """Combine user-selected import and export power entities."""

    _attr_has_entity_name = True
    _attr_name = "Kiválasztott nettó teljesítmény"
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:home-lightning-bolt"

    def __init__(
        self,
        entry: ConfigEntry,
        import_entity: str,
        export_entity: str,
    ) -> None:
        self._import_entity = import_entity
        self._export_entity = export_entity
        self._attr_unique_id = f"{DOMAIN}_{_source_key(entry)}_selected_net_power"
        self._attr_device_info = _device_info(entry)

    async def async_added_to_hass(self) -> None:
        """Track both selected power sources."""
        await super().async_added_to_hass()
        self.async_on_remove(
            async_track_state_change_event(
                self.hass,
                [self._import_entity, self._export_entity],
                self._async_source_changed,
            )
        )

    @callback
    def _async_source_changed(self, _event: Event[EventStateChangedData]) -> None:
        self.async_write_ha_state()

    def _power_watt(self, entity_id: str) -> float | None:
        state = self.hass.states.get(entity_id)
        if state is None or state.state in {"unknown", "unavailable"}:
            return None
        try:
            value = float(state.state)
            unit = state.attributes.get("unit_of_measurement")
            if not unit:
                return None
            return PowerConverter.convert(value, unit, UnitOfPower.WATT)
        except (HomeAssistantError, TypeError, ValueError):
            return None

    @property
    def available(self) -> bool:
        return (
            self._power_watt(self._import_entity) is not None
            and self._power_watt(self._export_entity) is not None
        )

    @property
    def native_value(self) -> float | None:
        imported = self._power_watt(self._import_entity)
        exported = self._power_watt(self._export_entity)
        if imported is None or exported is None:
            return None
        return round(imported - exported, 3)

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        return {
            "import_power_entity": self._import_entity,
            "export_power_entity": self._export_entity,
            "sign_convention": "import_positive_export_negative",
        }


class SlimmeLezerGridNetPowerSensor(
    CoordinatorEntity[SlimmeLezerCoordinator], SensorEntity
):
    """Represent signed net power at the external electricity grid."""

    _attr_has_entity_name = True
    _attr_name = "Hálózati nettó teljesítmény"
    _attr_native_unit_of_measurement = "kW"
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:transmission-tower"

    def __init__(
        self,
        coordinator: SlimmeLezerCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_{_source_key(entry)}_grid_net_power"
        self._attr_device_info = _device_info(entry)

    @property
    def available(self) -> bool:
        data = self.coordinator.data
        return (
            super().available
            and data.power_import_kw is not None
            and data.power_export_kw is not None
        )

    @property
    def native_value(self) -> float | None:
        data = self.coordinator.data
        if data.power_import_kw is None or data.power_export_kw is None:
            return None
        return data.power_import_kw - data.power_export_kw

    @property
    def extra_state_attributes(self) -> dict[str, float | str]:
        data = self.coordinator.data
        attributes: dict[str, float | str] = {
            "sign_convention": "import_positive_export_negative"
        }
        if data.power_import_kw is not None:
            attributes["import_power_kw"] = data.power_import_kw
        if data.power_export_kw is not None:
            attributes["export_power_kw"] = data.power_export_kw
        return attributes


class SlimmeLezerRegisterSensor(
    CoordinatorEntity[SlimmeLezerCoordinator], SensorEntity
):
    """Represent one discovered OBIS value or value group."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SlimmeLezerCoordinator,
        entry: ConfigEntry,
        key: str,
    ) -> None:
        super().__init__(coordinator)
        self._key = key
        initial = coordinator.data.registers[key]
        self._attr_name = initial.name
        self._attr_unique_id = f"{DOMAIN}_{_source_key(entry)}_{key}"
        self._attr_device_info = _device_info(entry)

    @property
    def _register(self) -> RegisterValue | None:
        return self.coordinator.data.registers.get(self._key)

    @property
    def available(self) -> bool:
        return super().available and self._register is not None

    @property
    def native_value(self) -> float | str | None:
        register = self._register
        return register.value if register is not None else None

    @property
    def native_unit_of_measurement(self) -> str | None:
        register = self._register
        if register is None:
            return None
        return "m³" if register.unit == "m3" else register.unit

    @property
    def device_class(self) -> SensorDeviceClass | None:
        register = self._register
        return (
            DEVICE_CLASSES.get(register.device_class) if register is not None else None
        )

    @property
    def state_class(self) -> SensorStateClass | None:
        register = self._register
        return STATE_CLASSES.get(register.state_class) if register is not None else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        register = self._register
        if register is None:
            return {}
        return {
            "obis_code": register.obis,
            "value_group": register.group_index + 1,
            "mapping": "documented" if register.known else "automatic",
        }


class SlimmeLezerDiagnosticSensor(
    CoordinatorEntity[SlimmeLezerCoordinator], SensorEntity
):
    """Expose privacy-safe discovery health counters."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_state_class = SensorStateClass.MEASUREMENT

    NAMES: ClassVar[dict[str, str]] = {
        "obis_count": "Megfigyelt OBIS-regiszterek",
        "dynamic_count": "Raw telegramból képzett szenzorok",
        "unknown_count": "Automatikusan felismert új OBIS-regiszterek",
        "telegram_length": "Raw telegram hossza",
        "reported_count": "GitHubra jelentett OBIS-szerkezetek",
    }

    def __init__(
        self,
        coordinator: SlimmeLezerCoordinator,
        entry: ConfigEntry,
        key: str,
    ) -> None:
        super().__init__(coordinator)
        self._key = key
        self._attr_name = self.NAMES[key]
        self._attr_unique_id = f"{DOMAIN}_{_source_key(entry)}_diagnostic_{key}"
        self._attr_device_info = _device_info(entry)

    @property
    def native_value(self) -> int:
        data = self.coordinator.data
        if self._key == "obis_count":
            return len(data.obis_codes)
        if self._key == "dynamic_count":
            return len(data.registers)
        if self._key == "unknown_count":
            return len(data.unknown_codes)
        if self._key == "reported_count":
            return (
                self.coordinator.reporter.reported_count
                if self.coordinator.reporter is not None
                else 0
            )
        return data.telegram_length

    @property
    def native_unit_of_measurement(self) -> str | None:
        return "karakter" if self._key == "telegram_length" else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        if self._key != "unknown_count":
            return {}
        return {
            "obis_codes": sorted(self.coordinator.data.unknown_codes),
            "reporting": (
                self.coordinator.reporter.mode
                if self.coordinator.reporter is not None
                else "manual"
            ),
        }
