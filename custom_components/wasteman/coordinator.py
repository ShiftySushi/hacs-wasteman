"""DataUpdateCoordinator for Wasteman."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_UPRN, DOMAIN
from .scrapers import Collection
from .scrapers.south_and_vale import SouthAndValeScraper

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(hours=2)


class WastemanCoordinator(DataUpdateCoordinator[list[Collection]]):
    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, config: dict) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )
        self._scraper = SouthAndValeScraper(uprn=config[CONF_UPRN])

    async def _async_update_data(self) -> list[Collection]:
        try:
            return await self._scraper.fetch()
        except Exception as err:
            raise UpdateFailed(f"Failed to fetch waste collection data: {err}") from err
