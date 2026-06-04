"""Config flow and options flow for Wasteman."""
from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CALENDAR_VARIANTS,
    COLLECTION_DAYS,
    CONF_CALENDAR_VARIANT,
    CONF_COLLECTION_DAY,
    CONF_COUNCIL,
    CONF_DISPLAY_FORMAT,
    CONF_EXCLUDED_TYPES,
    CONF_LOOKAHEAD_DAYS,
    CONF_SENSOR_PER_TYPE,
    CONF_TYPE_ALIASES,
    COUNCILS,
    COUNCIL_SOUTH_OXFORDSHIRE,
    COUNCIL_VALE_OF_WHITE_HORSE,
    DEFAULT_DISPLAY_FORMAT,
    DEFAULT_LOOKAHEAD_DAYS,
    DEFAULT_SENSOR_PER_TYPE,
    DISPLAY_FORMAT_COMBINED,
    DISPLAY_FORMAT_DATE,
    DISPLAY_FORMAT_DAYS,
    DOMAIN,
)

_DISPLAY_FORMAT_OPTIONS = {
    DISPLAY_FORMAT_COMBINED: "Combined — Wednesday 4 Jun 2025 (in 3 days)",
    DISPLAY_FORMAT_DATE: "Date only — Wednesday 4 Jun 2025",
    DISPLAY_FORMAT_DAYS: "Days only — in 3 days",
}


class WastemanConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the initial setup of a Wasteman entry."""

    VERSION = 1

    def __init__(self) -> None:
        self._data: dict = {}

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        if user_input is not None:
            self._data[CONF_COUNCIL] = user_input[CONF_COUNCIL]
            return await self.async_step_collection_schedule()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_COUNCIL): vol.In(COUNCILS),
            }),
        )

    async def async_step_collection_schedule(
        self, user_input: dict | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            self._data[CONF_COLLECTION_DAY] = user_input[CONF_COLLECTION_DAY].lower()
            self._data[CONF_CALENDAR_VARIANT] = user_input[CONF_CALENDAR_VARIANT].lower()
            council_name = COUNCILS[self._data[CONF_COUNCIL]]
            day = user_input[CONF_COLLECTION_DAY]
            variant = user_input[CONF_CALENDAR_VARIANT]
            title = f"{council_name} — {day} {variant}"
            return self.async_create_entry(title=title, data=self._data)

        return self.async_show_form(
            step_id="collection_schedule",
            data_schema=vol.Schema({
                vol.Required(CONF_COLLECTION_DAY): vol.In(COLLECTION_DAYS),
                vol.Required(CONF_CALENDAR_VARIANT): vol.In(CALENDAR_VARIANTS),
            }),
            errors=errors,
            description_placeholders={
                "council": COUNCILS[self._data[CONF_COUNCIL]],
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> WastemanOptionsFlow:
        return WastemanOptionsFlow(config_entry)


class WastemanOptionsFlow(config_entries.OptionsFlow):
    """Handle options (display customisation) for an existing Wasteman entry."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(self, user_input: dict | None = None) -> FlowResult:
        opts = self._config_entry.options

        if user_input is not None:
            # Parse comma-separated aliases string into dict
            raw_aliases = user_input.pop("type_aliases_raw", "")
            aliases: dict[str, str] = {}
            for line in raw_aliases.splitlines():
                line = line.strip()
                if "=" in line:
                    original, _, alias = line.partition("=")
                    aliases[original.strip()] = alias.strip()
            user_input[CONF_TYPE_ALIASES] = aliases

            # Parse comma-separated excluded types
            raw_excluded = user_input.pop("excluded_types_raw", "")
            excluded = [e.strip() for e in raw_excluded.split(",") if e.strip()]
            user_input[CONF_EXCLUDED_TYPES] = excluded

            return self.async_create_entry(title="", data=user_input)

        # Build alias hint from current aliases
        current_aliases: dict[str, str] = opts.get(CONF_TYPE_ALIASES, {})
        aliases_str = "\n".join(f"{k} = {v}" for k, v in current_aliases.items())

        current_excluded: list[str] = opts.get(CONF_EXCLUDED_TYPES, [])
        excluded_str = ", ".join(current_excluded)

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
                # Free-text fields parsed on submit
                vol.Optional("excluded_types_raw", default=excluded_str): str,
                vol.Optional("type_aliases_raw", default=aliases_str): str,
            }),
            description_placeholders={
                "excluded_hint": "Comma-separated waste types to hide, e.g: Garden waste, Glass",
                "aliases_hint": "One per line: Original name = Your label",
            },
        )
