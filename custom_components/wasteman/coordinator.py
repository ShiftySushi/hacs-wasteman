"""DataUpdateCoordinator for Wasteman."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_COLLECTION_DAY,
    CONF_CALENDAR_VARIANT,
    CONF_COUNCIL,
    COUNCIL_SOUTH_OXFORDSHIRE,
    COUNCIL_VALE_OF_WHITE_HORSE,
    DOMAIN,
)
from .scrapers import Collection
from .scrapers.south_and_vale import SouthAndValeScraper

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(hours=12)


def _build_scraper(config: dict) -> SouthAndValeScraper:
    council = config[CONF_COUNCIL]
    if council in (COUNCIL_SOUTH_OXFORDSHIRE, COUNCIL_VALE_OF_WHITE_HORSE):
        return SouthAndValeScraper(
            collection_day=config[CONF_COLLECTION_DAY],
            calendar_variant=config[CONF_CALENDAR_VARIANT],
        )
    raise ValueError(f"Unknown council: {council}")


class WastemanCoordinator(DataUpdateCoordinator[list[Collection]]):
    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, config: dict) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )
        self._scraper = _build_scraper(config)

    async def _async_update_data(self) -> list[Collection]:
        try:
            return await self._scraper.fetch()
        except Exception as err:
            raise UpdateFailed(f"Failed to fetch waste collection data: {err}") from err
