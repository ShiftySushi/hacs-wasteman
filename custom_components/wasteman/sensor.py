"""Wasteman sensor platform."""
from __future__ import annotations

from datetime import date

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_DISPLAY_FORMAT,
    CONF_EXCLUDED_TYPES,
    CONF_LOOKAHEAD_DAYS,
    CONF_SENSOR_PER_TYPE,
    CONF_TYPE_ALIASES,
    DEFAULT_DISPLAY_FORMAT,
    DEFAULT_LOOKAHEAD_DAYS,
    DEFAULT_SENSOR_PER_TYPE,
    DISPLAY_FORMAT_COMBINED,
    DISPLAY_FORMAT_DATE,
    DISPLAY_FORMAT_DAYS,
    DOMAIN,
)
from .coordinator import WastemanCoordinator
from .scrapers import Collection

_DATE_FMT = "%-d %b %Y"
_DAY_FMT = "%A"


def _format_date(d: date) -> str:
    return f"{d.strftime(_DAY_FMT)} {d.strftime(_DATE_FMT)}"


def _format_days(days: int) -> str:
    if days == 0:
        return "today"
    if days == 1:
        return "tomorrow"
    return f"in {days} days"


def _state_string(collection: Collection, fmt: str) -> str:
    days = collection.days_until
    if fmt == DISPLAY_FORMAT_DAYS:
        return _format_days(days)
    if fmt == DISPLAY_FORMAT_DATE:
        return _format_date(collection.date)
    return f"{_format_date(collection.date)} ({_format_days(days)})"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: WastemanCoordinator = hass.data[DOMAIN][entry.entry_id]
    opts = entry.options
    excluded: set[str] = set(opts.get(CONF_EXCLUDED_TYPES, []))
    aliases: dict[str, str] = opts.get(CONF_TYPE_ALIASES, {})
    display_fmt: str = opts.get(CONF_DISPLAY_FORMAT, DEFAULT_DISPLAY_FORMAT)
    sensor_per_type: bool = opts.get(CONF_SENSOR_PER_TYPE, DEFAULT_SENSOR_PER_TYPE)
    lookahead: int = opts.get(CONF_LOOKAHEAD_DAYS, DEFAULT_LOOKAHEAD_DAYS)

    if sensor_per_type:
        known_types = {
            c.waste_type
            for c in (coordinator.data or [])
            if c.waste_type not in excluded
        }
        entities: list[SensorEntity] = [
            WasteTypeSensor(coordinator, entry, wtype, aliases, display_fmt, excluded, lookahead)
            for wtype in sorted(known_types)
        ]
    else:
        entities = [AggregateSensor(coordinator, entry, aliases, display_fmt, excluded, lookahead)]

    async_add_entities(entities, update_before_add=True)


class _WastemanSensorBase(CoordinatorEntity[WastemanCoordinator], SensorEntity):
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: WastemanCoordinator,
        entry: ConfigEntry,
        aliases: dict[str, str],
        display_fmt: str,
        excluded: set[str],
        lookahead: int,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._aliases = aliases
        self._display_fmt = display_fmt
        self._excluded = excluded
        self._lookahead = lookahead

    def _visible_collections(self) -> list[Collection]:
        today = date.today()
        return [
            c for c in (self.coordinator.data or [])
            if c.waste_type not in self._excluded
            and c.date >= today
            and c.days_until <= self._lookahead
        ]

    def _label(self, waste_type: str) -> str:
        return self._aliases.get(waste_type, waste_type)


class WasteTypeSensor(_WastemanSensorBase):
    """One sensor tracking a single waste type."""

    def __init__(
        self,
        coordinator: WastemanCoordinator,
        entry: ConfigEntry,
        waste_type: str,
        aliases: dict[str, str],
        display_fmt: str,
        excluded: set[str],
        lookahead: int,
    ) -> None:
        super().__init__(coordinator, entry, aliases, display_fmt, excluded, lookahead)
        self._waste_type = waste_type
        self._attr_unique_id = f"{entry.entry_id}_{waste_type}"

    @property
    def name(self) -> str:
        return self._label(self._waste_type)

    @property
    def native_value(self) -> str | None:
        nxt = self._next()
        return _state_string(nxt, self._display_fmt) if nxt else None

    @property
    def icon(self) -> str:
        nxt = self._next()
        return (nxt.icon or "mdi:trash-can-outline") if nxt else "mdi:trash-can-outline"

    @property
    def extra_state_attributes(self) -> dict:
        nxt = self._next()
        upcoming = [
            {"date": c.date.isoformat(), "days_until": c.days_until}
            for c in self._visible_collections()
            if c.waste_type == self._waste_type
        ]
        attrs: dict = {"upcoming": upcoming}
        if nxt:
            attrs["description"] = nxt.description
            if nxt.date_changed:
                attrs["date_changed"] = True
                attrs["change_reason"] = nxt.change_reason
        return attrs

    def _next(self) -> Collection | None:
        today = date.today()
        return next(
            (c for c in (self.coordinator.data or [])
             if c.waste_type == self._waste_type and c.date >= today),
            None,
        )


class AggregateSensor(_WastemanSensorBase):
    """Single sensor showing the next collection across all non-excluded types."""

    def __init__(
        self,
        coordinator: WastemanCoordinator,
        entry: ConfigEntry,
        aliases: dict[str, str],
        display_fmt: str,
        excluded: set[str],
        lookahead: int,
    ) -> None:
        super().__init__(coordinator, entry, aliases, display_fmt, excluded, lookahead)
        self._attr_unique_id = f"{entry.entry_id}_next_collection"
        self._attr_name = "Next Collection"

    @property
    def native_value(self) -> str | None:
        nxt = next(iter(self._visible_collections()), None)
        if nxt is None:
            return None
        return f"{self._label(nxt.waste_type)}: {_state_string(nxt, self._display_fmt)}"

    @property
    def icon(self) -> str:
        nxt = next(iter(self._visible_collections()), None)
        return (nxt.icon or "mdi:trash-can-outline") if nxt else "mdi:trash-can-outline"

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "upcoming": [
                {
                    "date": c.date.isoformat(),
                    "days_until": c.days_until,
                    "waste_type": self._label(c.waste_type),
                }
                for c in self._visible_collections()
            ]
        }
