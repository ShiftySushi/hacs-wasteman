"""South Oxfordshire / Vale of White Horse waste collection scraper.

Fetches the iCal feed published by South & Vale councils (same feed for both).
The feed URL is determined by the user's collection day and calendar variant (V1/V2).

Updating when the council changes their calendar:
  - Edit SOUTH_AND_VALE_ICAL_URLS in const.py with the new Google Calendar IDs.
  - No other code changes required.
"""
from __future__ import annotations

import logging
from datetime import date

import aiohttp
from icalendar import Calendar  # type: ignore[import-untyped]

from . import BaseScraper, Collection
from ..const import SOUTH_AND_VALE_ICAL_URLS

_LOGGER = logging.getLogger(__name__)

_ICON_KEYWORDS: list[tuple[str, str]] = [
    ("garden",    "mdi:leaf"),
    ("food",      "mdi:food-apple"),
    ("recycl",    "mdi:recycle"),
    ("rubbish",   "mdi:trash-can"),
    ("refuse",    "mdi:trash-can"),
    ("glass",     "mdi:bottle-wine"),
    ("textile",   "mdi:tshirt-crew"),
    ("battery",   "mdi:battery"),
]


def _guess_icon(waste_type: str) -> str:
    lower = waste_type.lower()
    for keyword, icon in _ICON_KEYWORDS:
        if keyword in lower:
            return icon
    return "mdi:trash-can-outline"


class SouthAndValeScraper(BaseScraper):
    NAME = "South Oxfordshire / Vale of White Horse"
    DESCRIPTION = "Google Calendar iCal feed from southandvale.gov.uk"

    def __init__(self, collection_day: str, calendar_variant: str) -> None:
        key = (collection_day.lower(), calendar_variant.lower())
        if key not in SOUTH_AND_VALE_ICAL_URLS:
            raise ValueError(
                f"No iCal URL configured for {collection_day} {calendar_variant}. "
                "Check SOUTH_AND_VALE_ICAL_URLS in const.py."
            )
        self._url = SOUTH_AND_VALE_ICAL_URLS[key]

    async def fetch(self) -> list[Collection]:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                self._url,
                timeout=aiohttp.ClientTimeout(total=30),
                headers={"User-Agent": "Mozilla/5.0 (Home Assistant Wasteman)"},
            ) as resp:
                resp.raise_for_status()
                raw = await resp.read()

        cal = Calendar.from_ical(raw)
        today = date.today()
        collections: list[Collection] = []

        for component in cal.walk():
            if component.name != "VEVENT":
                continue
            dtstart = component.get("DTSTART")
            summary = str(component.get("SUMMARY", "Unknown")).strip()
            if dtstart is None:
                continue
            event_date = dtstart.dt
            if hasattr(event_date, "date"):
                event_date = event_date.date()
            if event_date >= today:
                collections.append(Collection(
                    date=event_date,
                    waste_type=summary,
                    icon=_guess_icon(summary),
                ))

        collections.sort(key=lambda c: c.date)
        _LOGGER.debug("Fetched %d upcoming collections", len(collections))
        return collections
