"""Wasteman calendar platform."""
from __future__ import annotations

from datetime import date, datetime, timedelta

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_NEXT_BINS_TYPES, CONF_TYPE_ALIASES, DEFAULT_NEXT_BINS_TYPES, DOMAIN
from .coordinator import WastemanCoordinator
from .scrapers import Collection


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: WastemanCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([WastemanCalendar(coordinator, entry)], update_before_add=True)


class WastemanCalendar(CoordinatorEntity[WastemanCoordinator], CalendarEntity):
    _attr_has_entity_name = True
    _attr_name = "Waste Collections"

    def __init__(self, coordinator: WastemanCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_calendar"

    def _whitelist(self) -> set[str]:
        return set(self._entry.options.get(CONF_NEXT_BINS_TYPES, DEFAULT_NEXT_BINS_TYPES))

    def _label(self, waste_type: str) -> str:
        aliases: dict[str, str] = self._entry.options.get(CONF_TYPE_ALIASES, {})
        return aliases.get(waste_type, waste_type)

    def _to_event(self, col: Collection) -> CalendarEvent:
        label = self._label(col.waste_type)
        return CalendarEvent(
            start=col.date,
            end=col.date + timedelta(days=1),
            summary=label,
            description=col.waste_type if col.waste_type != label else None,
        )

    @property
    def event(self) -> CalendarEvent | None:
        today = date.today()
        whitelist = self._whitelist()
        for col in self.coordinator.data or []:
            if col.waste_type in whitelist and col.date >= today:
                return self._to_event(col)
        return None

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        whitelist = self._whitelist()
        events: list[CalendarEvent] = []
        for col in self.coordinator.data or []:
            if col.waste_type not in whitelist:
                continue
            col_start = datetime.combine(col.date, datetime.min.time())
            col_end = col_start + timedelta(days=1)
            if col_end <= start_date or col_start >= end_date:
                continue
            events.append(self._to_event(col))
        return events
