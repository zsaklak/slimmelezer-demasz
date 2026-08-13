"""Config flow for SlimmeLezer Démász."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse, urlunparse

import voluptuous as vol
from homeassistant import config_entries, data_entry_flow
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    BooleanSelector,
    EntitySelector,
    EntitySelectorConfig,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)
from homeassistant.helpers.update_coordinator import UpdateFailed
from homeassistant.util.unit_conversion import PowerConverter

from .const import (
    CONF_GITHUB_AUTO_REPORT,
    CONF_GITHUB_TOKEN,
    CONF_POWER_EXPORT_ENTITY,
    CONF_POWER_IMPORT_ENTITY,
    CONF_RESOURCE_URL,
    CONF_SCAN_INTERVAL,
    DEFAULT_GITHUB_AUTO_REPORT,
    DEFAULT_RESOURCE_URL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MIN_SCAN_INTERVAL,
)
from .coordinator import async_fetch_telegram


def normalize_url(value: str) -> str:
    """Validate and normalize the local ESPHome endpoint URL."""
    parsed = urlparse(value.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise vol.Invalid("Érvényes http vagy https URL szükséges.")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise vol.Invalid(
            "A végpont URL-je nem tartalmazhat hitelesítést, queryt vagy fragmentet."
        )
    path = parsed.path.rstrip("/") or "/text_sensor/raw_dsmr_telegram"
    return urlunparse((parsed.scheme, parsed.netloc, path, "", "", ""))


def user_schema(default_url: str = DEFAULT_RESOURCE_URL) -> vol.Schema:
    """Return the user-step schema."""
    return vol.Schema(
        {
            vol.Required(CONF_RESOURCE_URL, default=default_url): TextSelector(
                TextSelectorConfig(type=TextSelectorType.URL)
            ),
            vol.Required(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
                vol.Coerce(int), vol.Range(min=MIN_SCAN_INTERVAL, max=300)
            ),
        }
    )


class SlimmeLezerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SlimmeLezer Démász."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        _config_entry: config_entries.ConfigEntry,
    ) -> SlimmeLezerOptionsFlow:
        """Return the reporting options flow."""
        return SlimmeLezerOptionsFlow()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> data_entry_flow.FlowResult:
        """Handle the initial setup step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                resource_url = normalize_url(user_input[CONF_RESOURCE_URL])
            except vol.Invalid:
                errors[CONF_RESOURCE_URL] = "invalid_url"
            if not errors:
                try:
                    await async_fetch_telegram(self.hass, resource_url)
                except UpdateFailed:
                    errors["base"] = "cannot_connect"
                else:
                    parsed = urlparse(resource_url)
                    await self.async_set_unique_id(
                        f"{parsed.hostname}:{parsed.port or (443 if parsed.scheme == 'https' else 80)}"
                    )
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title=f"SlimmeLezer Démász ({parsed.hostname})",
                        data={
                            CONF_RESOURCE_URL: resource_url,
                            CONF_SCAN_INTERVAL: user_input[CONF_SCAN_INTERVAL],
                        },
                    )

        return self.async_show_form(
            step_id="user",
            data_schema=user_schema(
                user_input.get(CONF_RESOURCE_URL, DEFAULT_RESOURCE_URL)
                if user_input
                else DEFAULT_RESOURCE_URL
            ),
            errors=errors,
        )


class SlimmeLezerOptionsFlow(config_entries.OptionsFlowWithReload):
    """Configure optional power sources and privacy-safe reporting."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> data_entry_flow.FlowResult:
        """Manage integration options."""
        errors: dict[str, str] = {}
        current_token = self.config_entry.options.get(CONF_GITHUB_TOKEN, "")

        if user_input is not None:
            automatic = bool(user_input[CONF_GITHUB_AUTO_REPORT])
            submitted_token = user_input.get(CONF_GITHUB_TOKEN, "").strip()
            token = submitted_token or current_token
            import_entity = user_input.get(CONF_POWER_IMPORT_ENTITY)
            export_entity = user_input.get(CONF_POWER_EXPORT_ENTITY)
            if automatic and not token:
                errors[CONF_GITHUB_TOKEN] = "token_required"
            elif bool(import_entity) != bool(export_entity):
                errors["base"] = "power_pair_required"
            elif import_entity and import_entity == export_entity:
                errors["base"] = "power_entities_must_differ"
            elif import_entity and not self._valid_power_entity(import_entity):
                errors[CONF_POWER_IMPORT_ENTITY] = "invalid_power_entity"
            elif export_entity and not self._valid_power_entity(export_entity):
                errors[CONF_POWER_EXPORT_ENTITY] = "invalid_power_entity"
            else:
                options: dict[str, Any] = {
                    CONF_GITHUB_AUTO_REPORT: automatic,
                }
                if automatic:
                    options[CONF_GITHUB_TOKEN] = token
                if import_entity and export_entity:
                    options[CONF_POWER_IMPORT_ENTITY] = import_entity
                    options[CONF_POWER_EXPORT_ENTITY] = export_entity
                return self.async_create_entry(title="", data=options)

        schema_fields: dict[vol.Marker, Any] = {
            vol.Required(
                CONF_GITHUB_AUTO_REPORT,
                default=self.config_entry.options.get(
                    CONF_GITHUB_AUTO_REPORT, DEFAULT_GITHUB_AUTO_REPORT
                ),
            ): BooleanSelector(),
            vol.Optional(CONF_GITHUB_TOKEN): TextSelector(
                TextSelectorConfig(type=TextSelectorType.PASSWORD)
            ),
        }
        power_selector = EntitySelector(
            EntitySelectorConfig(filter={"domain": "sensor", "device_class": "power"})
        )
        current_import = self.config_entry.options.get(CONF_POWER_IMPORT_ENTITY)
        current_export = self.config_entry.options.get(CONF_POWER_EXPORT_ENTITY)
        schema_fields[
            vol.Optional(
                CONF_POWER_IMPORT_ENTITY,
                **({"default": current_import} if current_import else {}),
            )
        ] = power_selector
        schema_fields[
            vol.Optional(
                CONF_POWER_EXPORT_ENTITY,
                **({"default": current_export} if current_export else {}),
            )
        ] = power_selector
        schema = vol.Schema(schema_fields)
        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "token_status": ("már elmentve" if current_token else "nincs elmentve")
            },
        )

    def _valid_power_entity(self, entity_id: str) -> bool:
        """Return whether the selected entity currently represents power."""
        state = self.hass.states.get(entity_id)
        return (
            state is not None
            and state.domain == "sensor"
            and state.attributes.get("device_class") == "power"
            and state.attributes.get("unit_of_measurement")
            in PowerConverter.VALID_UNITS
        )
