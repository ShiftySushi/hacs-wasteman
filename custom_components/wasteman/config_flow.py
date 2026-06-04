"""Config flow and options flow for Wasteman."""
from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_DISPLAY_FORMAT,
    CONF_EXCLUDED_TYPES,
    CONF_LOOKAHEAD_DAYS,
    CONF_POSTCODE,
    CONF_SENSOR_PER_TYPE,
    CONF_TYPE_ALIASES,
    CONF_UPRN,
    DEFAULT_DISPLAY_FORMAT,
    DEFAULT_LOOKAHEAD_DAYS,
    DEFAULT_SENSOR_PER_TYPE,
    DISPLAY_FORMAT_COMBINED,
    DISPLAY_FORMAT_DATE,
    DISPLAY_FORMAT_DAYS,
    DOMAIN,
)
from .scrapers.south_and_vale import lookup_addresses

_DISPLAY_FORMAT_OPTIONS = {
    DISPLAY_FORMAT_COMBINED: "Combined — Wednesday 4 Jun 2026 (in 3 days)",
    DISPLAY_FORMAT_DATE: "Date only — Wednesday 4 Jun 2026",
    DISPLAY_FORMAT_DAYS: "Days only — in 3 days",
}


class WastemanConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Two-step setup: postcode → address selection."""

    VERSION = 1

    def __init__(self) -> None:
        self._postcode: str = ""
        self._addresses: list[dict] = []

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            postcode = user_input[CONF_POSTCODE].strip()
            try:
                self._addresses = await lookup_addresses(postcode)
                self._postcode = postcode
                return await self.async_step_address()
            except Exception:  # noqa: BLE001
                errors["base"] = "postcode_not_found"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_POSTCODE): str,
            }),
            errors=errors,
        )

    async def async_step_address(self, user_input: dict | None = None) -> FlowResult:
        if user_input is not None:
            uprn = user_input[CONF_UPRN]
            address_label = next(
                a["address"] for a in self._addresses if a["uprn"] == uprn
            )
            return self.async_create_entry(
                title=address_label,
                data={CONF_UPRN: uprn, CONF_POSTCODE: self._postcode},
            )

        address_map = {a["uprn"]: a["address"] for a in self._addresses}

        # If there's only one address skip selection entirely
        if len(address_map) == 1:
            [(uprn, label)] = address_map.items()
            return self.async_create_entry(
                title=label,
                data={CONF_UPRN: uprn, CONF_POSTCODE: self._postcode},
            )

        return self.async_show_form(
            step_id="address",
            data_schema=vol.Schema({
                vol.Required(CONF_UPRN): vol.In(address_map),
            }),
            description_placeholders={"postcode": self._postcode},
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> WastemanOptionsFlow:
        return WastemanOptionsFlow(config_entry)


class WastemanOptionsFlow(config_entries.OptionsFlow):
    """Customisation: display format, aliases, exclusions."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(self, user_input: dict | None = None) -> FlowResult:
        opts = self._config_entry.options

        if user_input is not None:
            raw_aliases = user_input.pop("type_aliases_raw", "")
            aliases: dict[str, str] = {}
            for line in raw_aliases.splitlines():
                if "=" in line:
                    original, _, alias = line.partition("=")
                    aliases[original.strip()] = alias.strip()
            user_input[CONF_TYPE_ALIASES] = aliases

            raw_excluded = user_input.pop("excluded_types_raw", "")
            user_input[CONF_EXCLUDED_TYPES] = [e.strip() for e in raw_excluded.split(",") if e.strip()]

            return self.async_create_entry(title="", data=user_input)

        current_aliases: dict[str, str] = opts.get(CONF_TYPE_ALIASES, {})
        aliases_str = "\n".join(f"{k} = {v}" for k, v in current_aliases.items())
        excluded_str = ", ".join(opts.get(CONF_EXCLUDED_TYPES, []))

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional(
                    CONF_DISPLAY_FORMAT,
                    default=opts.get(CONF_DISPLAY_FORMAT, DEFAULT_DISPLAY_FORMAT),
                ): vol.In(_DISPLAY_FORMAT_OPTIONS),
                vol.Optional(
                    CONF_SENSOR_PER_TYPE,
                    default=opts.get(CONF_SENSOR_PER_TYPE, DEFAULT_SENSOR_PER_TYPE),
                ): bool,
                vol.Optional(
                    CONF_LOOKAHEAD_DAYS,
                    default=opts.get(CONF_LOOKAHEAD_DAYS, DEFAULT_LOOKAHEAD_DAYS),
                ): vol.All(int, vol.Range(min=1, max=365)),
                vol.Optional("excluded_types_raw", default=excluded_str): str,
                vol.Optional("type_aliases_raw", default=aliases_str): str,
            }),
        )
