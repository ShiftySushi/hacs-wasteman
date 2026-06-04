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
    CONF_LOOKAHEAD_DAYS,
    CONF_NEXT_BINS_TYPES,
    CONF_SENSOR_PER_TYPE,
    CONF_SEPARATOR,
    CONF_TYPE_ALIASES,
    DEFAULT_DISPLAY_FORMAT,
    DEFAULT_LOOKAHEAD_DAYS,
    DEFAULT_NEXT_BINS_TYPES,
    DEFAULT_SENSOR_PER_TYPE,
    DEFAULT_SEPARATOR,
    DISPLAY_FORMAT_COMBINED,
    DISPLAY_FORMAT_DATE,
    DISPLAY_FORMAT_DAYS,
    DOMAIN,
)
from .coordinator import WastemanCoordinator
from .scrapers import Collection

_DATE_FMT = "%-d %b %Y"
_DAY_FMT = "%A"


# --- Formatting helpers ---

def _format_date(d: date) -> str:
    return f"{d.strftime(_DAY_FMT)} {d.strftime(_DATE_FMT)}"


def _format_days(days: int) -> str:
    if days == 0:
        return "today"
    if days == 1:
        return "tomorrow"
    return f"in {days} days"


def _format_days_short(days: int) -> str:
    if days == 0:
        return "today"
    if days == 1:
        return "tomorrow"
    return f"{days} days"


def _state_string(collection: Collection, fmt: str) -> str:
    days = collection.days_until
    if fmt == DISPLAY_FORMAT_DAYS:
        return _format_days(days)
    if fmt == DISPLAY_FORMAT_DATE:
        return _format_date(collection.date)
    return f"{_format_date(collection.date)} ({_format_days(days)})"


def _group_by_date(collections: list[Collection]) -> dict[date, list[Collection]]:
    groups: dict[date, list[Collection]] = {}
    for c in collections:
        groups.setdefault(c.date, []).append(c)
    return groups


# --- Entity setup ---

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: WastemanCoordinator = hass.data[DOMAIN][entry.entry_id]
    opts = entry.options
    whitelist: list[str] = opts.get(CONF_NEXT_BINS_TYPES, DEFAULT_NEXT_BINS_TYPES)
    whitelist_set = set(whitelist)
    aliases: dict[str, str] = opts.get(CONF_TYPE_ALIASES, {})
    display_fmt: str = opts.get(CONF_DISPLAY_FORMAT, DEFAULT_DISPLAY_FORMAT)
    sensor_per_type: bool = opts.get(CONF_SENSOR_PER_TYPE, DEFAULT_SENSOR_PER_TYPE)
    lookahead: int = opts.get(CONF_LOOKAHEAD_DAYS, DEFAULT_LOOKAHEAD_DAYS)
    separator: str = opts.get(CONF_SEPARATOR, DEFAULT_SEPARATOR)

    # Combined sensor is always created.
    entities: list[SensorEntity] = [
        NextBinsSensor(coordinator, entry, aliases, whitelist_set, lookahead, separator)
    ]

    # Per-type sensors: created for every whitelisted type.
    # Using the whitelist (not coordinator.data) guarantees sensors exist even if
    # the API only returned one collection cycle at setup time.
    if sensor_per_type:
        entities.extend(
            WasteTypeSensor(coordinator, entry, wtype, aliases, display_fmt, lookahead)
            for wtype in sorted(whitelist_set)
        )

    async_add_entities(entities, update_before_add=True)


# --- Base class ---

class _WastemanSensorBase(CoordinatorEntity[WastemanCoordinator], SensorEntity):
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: WastemanCoordinator,
        entry: ConfigEntry,
        aliases: dict[str, str],
        lookahead: int,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._aliases = aliases
        self._lookahead = lookahead

    def _label(self, waste_type: str) -> str:
        return self._aliases.get(waste_type, waste_type)

    def _collections_for(self, *types: str) -> list[Collection]:
        """Upcoming collections for the given waste types within the lookahead window."""
        type_set = set(types)
        today = date.today()
        return [
            c for c in (self.coordinator.data or [])
            if c.waste_type in type_set
            and c.date >= today
            and c.days_until <= self._lookahead
        ]


# --- Combined sensor ---

class NextBinsSensor(_WastemanSensorBase):
    """Shows all whitelisted waste types due on the next collection date.

    State: "Recycling, Garden Waste, Food Waste - 3 days"
    """

    def __init__(
        self,
        coordinator: WastemanCoordinator,
        entry: ConfigEntry,
        aliases: dict[str, str],
        whitelist: set[str],
        lookahead: int,
        separator: str,
    ) -> None:
        super().__init__(coordinator, entry, aliases, lookahead)
        self._whitelist = whitelist
        self._separator = separator
        self._attr_unique_id = f"{entry.entry_id}_next_bins"
        self._attr_name = "Next Bins"
        self._attr_icon = "mdi:trash-can"

    def _visible(self) -> list[Collection]:
        today = date.today()
        return [
            c for c in (self.coordinator.data or [])
            if c.waste_type in self._whitelist
            and c.date >= today
            and c.days_until <= self._lookahead
        ]

    @property
    def native_value(self) -> str | None:
        visible = self._visible()
        if not visible:
            return None
        groups = _group_by_date(visible)
        next_date = min(groups)
        items = groups[next_date]
        labels = self._separator.join(self._label(c.waste_type) for c in items)
        return f"{labels} - {_format_days_short(items[0].days_until)}"

    @property
    def extra_state_attributes(self) -> dict:
        groups = _group_by_date(self._visible())
        return {
            "upcoming": [
                {
                    "date": d.isoformat(),
                    "days_until": items[0].days_until,
                    "waste_types": [self._label(c.waste_type) for c in items],
                    "date_changed": any(c.date_changed for c in items),
                }
                for d, items in sorted(groups.items())
            ]
        }


# --- Per-type sensor ---

class WasteTypeSensor(_WastemanSensorBase):
    """One sensor tracking a single waste type."""

    def __init__(
        self,
        coordinator: WastemanCoordinator,
        entry: ConfigEntry,
        waste_type: str,
        aliases: dict[str, str],
        display_fmt: str,
        lookahead: int,
    ) -> None:
        super().__init__(coordinator, entry, aliases, lookahead)
        self._waste_type = waste_type
        self._display_fmt = display_fmt
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
            for c in self._collections_for(self._waste_type)
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
