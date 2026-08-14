"""Runtime tests for the Home Assistant custom integration."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest
import voluptuous_serialize
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import UnitOfPower
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.update_coordinator import UpdateFailed
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.slimmelezer_demasz.const import (
    CONF_GITHUB_AUTO_REPORT,
    CONF_GITHUB_TOKEN,
    CONF_POWER_EXPORT_ENTITY,
    CONF_POWER_IMPORT_ENTITY,
    CONF_RESOURCE_URL,
    CONF_SCAN_INTERVAL,
    DOMAIN,
    EVENT_NEW_OBIS,
    GITHUB_ISSUES_API_URL,
)
from custom_components.slimmelezer_demasz.coordinator import (
    SlimmeLezerCoordinator,
    TelegramFetchError,
    async_fetch_telegram,
)
from custom_components.slimmelezer_demasz.parser import parse_telegram
from custom_components.slimmelezer_demasz.reporting import repair_issue_id

URL = "http://192.0.2.1/text_sensor/raw_dsmr_telegram"
PROFILE = (
    "(260801000000S)"
    "(1*kWh)(2*kWh)(3*kWh)(4*kWh)(5*kWh)(6*kWh)"
    "(7*kvarh)(8*kvarh)(9*kvarh)(10*kvarh)(11*kvarh)(12*kvarh)"
    "(13*kWh)(14*kW)(15*kW)(16*kW)(17*kW)(18*kW)(19*kW)"
)


def telegram(*extra_lines: str) -> str:
    """Return a fabricated complete telegram with all 31 raw sensors."""
    lines = [
        "0-0:1.0.0(260811120000S)",
        "0-0:42.0.0(53414735)",
        "0-0:96.1.0(303132333435)",
        "1-0:1.7.0(0.250*kW)",
        "1-0:2.7.0(0.750*kW)",
        "1-0:5.7.0(1*kvar)",
        "1-0:6.7.0(2*kvar)",
        "1-0:7.7.0(3*kvar)",
        "1-0:8.7.0(4*kvar)",
        "1-0:5.8.0(5*kvarh)",
        "1-0:6.8.0(6*kvarh)",
        "1-0:7.8.0(7*kvarh)",
        "1-0:8.8.0(8*kvarh)",
        "1-0:15.8.0(9*kWh)",
        f"0-0:98.1.0{PROFILE}",
        *extra_lines,
    ]
    return "/SAG5SAG-METER\r\n\r\n" + "\r\n".join(lines) + "\r\n!ABCD\r\n"


async def test_fetch_retries_one_transient_failure(hass) -> None:
    """Retry one failed endpoint request before failing the refresh."""
    expected = parse_telegram(telegram())
    failure = TelegramFetchError("http_timeout", "TimeoutError", "teszt időtúllépés")
    with (
        patch(
            "custom_components.slimmelezer_demasz.coordinator."
            "_async_fetch_telegram_once",
            new=AsyncMock(side_effect=[failure, expected]),
        ) as fetch,
        patch(
            "custom_components.slimmelezer_demasz.coordinator.asyncio.sleep",
            new=AsyncMock(),
        ) as sleep,
    ):
        result = await async_fetch_telegram(hass, URL)

    assert result is expected
    assert fetch.await_count == 2
    sleep.assert_awaited_once()


async def test_coordinator_keeps_last_good_data_for_two_failed_refreshes(
    hass,
) -> None:
    """Keep entities available for two failed refreshes, then surface failure."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_RESOURCE_URL: URL, CONF_SCAN_INTERVAL: 10},
    )
    coordinator = SlimmeLezerCoordinator(hass, entry)
    expected = parse_telegram(telegram())
    coordinator.async_set_updated_data(expected)
    failure = TelegramFetchError("http_timeout", "TimeoutError", "teszt időtúllépés")

    with patch(
        "custom_components.slimmelezer_demasz.coordinator.async_fetch_telegram",
        new=AsyncMock(side_effect=[failure, failure, failure]),
    ):
        assert await coordinator._async_update_data() is expected
        assert await coordinator._async_update_data() is expected
        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()

    assert coordinator.consecutive_failed_refreshes == 3
    assert coordinator.total_failed_refreshes == 3
    assert coordinator.stale_refreshes == 2
    assert not coordinator.using_stale_data
    assert coordinator.last_failure_stage == "http_timeout"
    assert coordinator.last_failure_type == "TimeoutError"


async def test_coordinator_resets_stale_state_after_recovery(hass) -> None:
    """Clear the consecutive-failure state after a successful refresh."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_RESOURCE_URL: URL, CONF_SCAN_INTERVAL: 10},
    )
    coordinator = SlimmeLezerCoordinator(hass, entry)
    expected = parse_telegram(telegram())
    coordinator.async_set_updated_data(expected)
    failure = TelegramFetchError("http", "ClientError", "teszt HTTP-hiba")

    with patch(
        "custom_components.slimmelezer_demasz.coordinator.async_fetch_telegram",
        new=AsyncMock(side_effect=[failure, expected]),
    ):
        assert await coordinator._async_update_data() is expected
        assert coordinator.using_stale_data
        assert await coordinator._async_update_data() is expected

    assert coordinator.consecutive_failed_refreshes == 0
    assert coordinator.total_failed_refreshes == 1
    assert coordinator.stale_refreshes == 1
    assert not coordinator.using_stale_data


async def test_config_flow_validates_the_raw_endpoint(hass, aioclient_mock) -> None:
    """Validate the endpoint before creating a unique config entry."""
    aioclient_mock.get(URL, json={"value": telegram()})

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    assert result["type"] is FlowResultType.FORM
    assert voluptuous_serialize.convert(
        result["data_schema"], custom_serializer=cv.custom_serializer
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_RESOURCE_URL: URL, CONF_SCAN_INTERVAL: 10},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        CONF_RESOURCE_URL: URL,
        CONF_SCAN_INTERVAL: 10,
    }


async def test_config_flow_rejects_unsafe_url_without_crashing(hass) -> None:
    """Return a field error for URLs containing credentials."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_RESOURCE_URL: "http://user:secret@192.0.2.1/raw",
            CONF_SCAN_INTERVAL: 10,
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {CONF_RESOURCE_URL: "invalid_url"}


async def test_setup_and_runtime_discovery(hass, aioclient_mock) -> None:
    """Create 31+1+5 entities, then add an OBIS entity and Repair live."""
    aioclient_mock.get(URL, json={"value": telegram()})
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="SlimmeLezer Démász",
        unique_id="192.0.2.1:80",
        data={CONF_RESOURCE_URL: URL, CONF_SCAN_INTERVAL: 10},
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.LOADED
    assert len(hass.states.async_all("sensor")) == 37
    net_power = next(
        state
        for state in hass.states.async_all("sensor")
        if state.attributes.get("sign_convention") == "import_positive_export_negative"
    )
    assert net_power.state == "-0.5"
    assert net_power.attributes["unit_of_measurement"] == "kW"
    assert net_power.attributes["device_class"] == "power"
    assert net_power.attributes["state_class"] == "measurement"
    assert net_power.attributes["import_power_kw"] == 0.25
    assert net_power.attributes["export_power_kw"] == 0.75
    device = next(
        item
        for item in dr.async_get(hass).devices.values()
        if any(identifier[0] == DOMAIN for identifier in item.identifiers)
    )
    assert device.manufacturer == "Sagem"
    assert device.model == "MA309M + SlimmeLezer"

    events = []
    hass.bus.async_listen(EVENT_NEW_OBIS, events.append)

    entry.runtime_data.async_set_updated_data(
        parse_telegram(telegram("1-0:14.7.0(50.000*Hz)"))
    )
    await hass.async_block_till_done()

    states = hass.states.async_all("sensor")
    assert len(states) == 38
    discovered = [
        state for state in states if state.attributes.get("obis_code") == "1-0:14.7.0"
    ]
    assert len(discovered) == 1
    assert discovered[0].state == "50.0"
    assert discovered[0].attributes["device_class"] == "frequency"
    assert len(events) == 1
    assert events[0].data["obis"] == "1-0:14.7.0"
    assert "50.0" not in str(events[0].data)

    issue = ir.async_get(hass).async_get_issue(
        DOMAIN, repair_issue_id(entry, "1-0:14.7.0")
    )
    assert issue is not None
    assert "1-0%3A14.7.0" in issue.learn_more_url


async def test_automatic_github_reporting_is_opt_in_and_deduplicated(
    hass, aioclient_mock
) -> None:
    """Submit one value-free issue and remember its structural fingerprint."""
    aioclient_mock.get(URL, json={"value": telegram()})
    aioclient_mock.post(
        GITHUB_ISSUES_API_URL,
        json={"html_url": "https://github.com/zsaklak/slimmelezer-demasz/issues/1"},
        status=201,
    )
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="SlimmeLezer Démász",
        unique_id="192.0.2.1:80",
        data={CONF_RESOURCE_URL: URL, CONF_SCAN_INTERVAL: 10},
        options={
            CONF_GITHUB_AUTO_REPORT: True,
            CONF_GITHUB_TOKEN: "test-token",
        },
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    unknown = parse_telegram(telegram("9-9:1.2.3(12345.678*mystery)"))
    entry.runtime_data.async_set_updated_data(unknown)
    await hass.async_block_till_done()
    assert entry.runtime_data.reporter.reported_count == 1

    await entry.runtime_data.reporter.async_report_codes(unknown, ["9-9:1.2.3"])
    assert entry.runtime_data.reporter.reported_count == 1

    github_calls = [
        call
        for call in aioclient_mock.mock_calls
        if str(call[1]) == GITHUB_ISSUES_API_URL
    ]
    assert len(github_calls) == 1
    payload = github_calls[0][2]
    assert "12345.678" not in json.dumps(payload)
    assert "192.0.2.1" not in json.dumps(payload)


async def test_options_require_token_only_for_automatic_mode(
    hass, aioclient_mock
) -> None:
    """Keep manual reporting token-free and protect automatic submission."""
    aioclient_mock.get(URL, json={"value": telegram()})
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="SlimmeLezer Démász",
        unique_id="192.0.2.1:80",
        data={CONF_RESOURCE_URL: URL, CONF_SCAN_INTERVAL: 10},
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {CONF_GITHUB_AUTO_REPORT: True, CONF_GITHUB_TOKEN: ""},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {CONF_GITHUB_TOKEN: "token_required"}

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {CONF_GITHUB_AUTO_REPORT: False, CONF_GITHUB_TOKEN: ""},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {CONF_GITHUB_AUTO_REPORT: False}
    await hass.async_block_till_done()
    await hass.config_entries.async_unload(entry.entry_id)


async def test_options_require_a_valid_distinct_power_pair(
    hass, aioclient_mock
) -> None:
    """Accept only two different power-class sensor entities."""
    aioclient_mock.get(URL, json={"value": telegram()})
    hass.states.async_set(
        "sensor.import_power",
        "1.2",
        {
            "device_class": SensorDeviceClass.POWER,
            "unit_of_measurement": UnitOfPower.KILO_WATT,
        },
    )
    hass.states.async_set(
        "sensor.export_power",
        "300",
        {
            "device_class": SensorDeviceClass.POWER,
            "unit_of_measurement": UnitOfPower.WATT,
        },
    )
    hass.states.async_set(
        "sensor.invalid_power",
        "10",
        {
            "device_class": SensorDeviceClass.POWER,
            "unit_of_measurement": "alma",
        },
    )
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="SlimmeLezer Démász",
        unique_id="192.0.2.1:80",
        data={CONF_RESOURCE_URL: URL, CONF_SCAN_INTERVAL: 10},
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert voluptuous_serialize.convert(
        result["data_schema"], custom_serializer=cv.custom_serializer
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_GITHUB_AUTO_REPORT: False,
            CONF_POWER_IMPORT_ENTITY: "sensor.import_power",
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "power_pair_required"}

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_GITHUB_AUTO_REPORT: False,
            CONF_POWER_IMPORT_ENTITY: "sensor.import_power",
            CONF_POWER_EXPORT_ENTITY: "sensor.import_power",
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "power_entities_must_differ"}

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_GITHUB_AUTO_REPORT: False,
            CONF_POWER_IMPORT_ENTITY: "sensor.invalid_power",
            CONF_POWER_EXPORT_ENTITY: "sensor.export_power",
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {CONF_POWER_IMPORT_ENTITY: "invalid_power_entity"}

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_GITHUB_AUTO_REPORT: False,
            CONF_POWER_IMPORT_ENTITY: "sensor.import_power",
            CONF_POWER_EXPORT_ENTITY: "sensor.export_power",
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        CONF_GITHUB_AUTO_REPORT: False,
        CONF_POWER_IMPORT_ENTITY: "sensor.import_power",
        CONF_POWER_EXPORT_ENTITY: "sensor.export_power",
    }
    await hass.async_block_till_done()
    await hass.config_entries.async_unload(entry.entry_id)


async def test_selected_power_entities_create_a_live_net_sensor(
    hass, aioclient_mock
) -> None:
    """Normalize mixed units and update when either selected source changes."""
    aioclient_mock.get(URL, json={"value": telegram()})
    hass.states.async_set(
        "sensor.import_power",
        "1.2",
        {
            "device_class": SensorDeviceClass.POWER,
            "unit_of_measurement": UnitOfPower.KILO_WATT,
        },
    )
    hass.states.async_set(
        "sensor.export_power",
        "300",
        {
            "device_class": SensorDeviceClass.POWER,
            "unit_of_measurement": UnitOfPower.WATT,
        },
    )
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="SlimmeLezer Démász",
        unique_id="192.0.2.1:80",
        data={CONF_RESOURCE_URL: URL, CONF_SCAN_INTERVAL: 10},
        options={
            CONF_GITHUB_AUTO_REPORT: False,
            CONF_POWER_IMPORT_ENTITY: "sensor.import_power",
            CONF_POWER_EXPORT_ENTITY: "sensor.export_power",
        },
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    selected = next(
        state
        for state in hass.states.async_all("sensor")
        if state.attributes.get("import_power_entity") == "sensor.import_power"
    )
    assert selected.state == "900.0"
    assert selected.attributes["unit_of_measurement"] == "W"
    assert selected.attributes["device_class"] == "power"
    assert selected.attributes["state_class"] == "measurement"

    hass.states.async_set(
        "sensor.export_power",
        "500",
        {
            "device_class": SensorDeviceClass.POWER,
            "unit_of_measurement": UnitOfPower.WATT,
        },
    )
    await hass.async_block_till_done()
    assert hass.states.get(selected.entity_id).state == "700.0"

    hass.states.async_set(
        "sensor.export_power",
        "unavailable",
        {
            "device_class": SensorDeviceClass.POWER,
            "unit_of_measurement": UnitOfPower.WATT,
        },
    )
    await hass.async_block_till_done()
    assert hass.states.get(selected.entity_id).state == "unavailable"
