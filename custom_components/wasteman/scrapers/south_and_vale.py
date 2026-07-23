"""South Oxfordshire / Vale of White Horse waste collection scraper.

Uses the BinDays REST API at forms.southandvale.gov.uk — no session or auth required.

Two endpoints:
  POST /api/property/postcode/{POSTCODE}  → list of {uprn, address, council}
  GET  /api/property/bins/{UPRN}          → upcoming collection weeks with bin types and dates

Updating when the council migrates their system:
  Edit BINDAYS_BASE / BINDAYS_POSTCODE_URL / BINDAYS_BINS_URL in const.py.
  The data parsing in this file may also need updating if the JSON structure changes.
"""
from __future__ import annotations

import logging
from datetime import date, datetime

from aiohttp import ClientSession, ClientTimeout
from homeassistant.util import dt as dt_util

from . import BaseScraper, Collection
from ..const import BINDAYS_BINS_URL, BINDAYS_POSTCODE_URL

_LOGGER = logging.getLogger(__name__)

_ICON_KEYWORDS: list[tuple[str, str]] = [
    ("garden",    "mdi:tree"),
    ("food",      "mdi:food-apple"),
    ("recycl",    "mdi:recycle"),
    ("refuse",    "mdi:trash-can"),
    ("rubbish",   "mdi:trash-can"),
    ("glass",     "mdi:bottle-wine"),
    ("textile",   "mdi:tshirt-crew"),
    ("cloth",     "mdi:tshirt-crew"),
    ("batter",    "mdi:battery"),
    ("electric",  "mdi:power-plug"),
    ("bulky",     "mdi:sofa"),
]

_HEADERS = {"User-Agent": "Mozilla/5.0 (Home Assistant Wasteman)"}

# Maps lowercase raw API bin_type → clean display name.
# Add entries here if the council changes their naming in the API response.
_WASTE_TYPE_NAMES: dict[str, str] = {
    "recycling":                      "Recycling",
    "garden waste subscribers":       "Garden Waste",
    "food waste":                     "Food Waste",
    "non-recyclable refuse waste":    "Refuse",
    "textiles/clothes":               "Textiles",
    "batteries":                      "Batteries",
    "small electricals":              "Small Electricals",
    "bulky waste":                    "Bulky Waste",
    "non-electrical bulky waste":     "Bulky Waste (Non-Electrical)",
}


def _normalize_waste_type(raw: str) -> str:
    """Return a clean, consistently capitalised waste type name."""
    stripped = raw.strip()
    return _WASTE_TYPE_NAMES.get(stripped.lower(), stripped.title())


def _guess_icon(bin_type: str) -> str:
    lower = bin_type.lower()
    for keyword, icon in _ICON_KEYWORDS:
        if keyword in lower:
            return icon
    return "mdi:trash-can-outline"


def _parse_date(date_str: str) -> date | None:
    try:
        return datetime.strptime(date_str, "%d/%m/%Y").date()
    except (ValueError, TypeError):
        return None


async def lookup_addresses(session: ClientSession, postcode: str) -> list[dict]:
    """Return [{uprn, address, council}, ...] for a postcode.

    Raises ValueError if the postcode returns no results or the API errors.
    """
    clean = postcode.replace(" ", "").upper()
    url = BINDAYS_POSTCODE_URL.format(postcode=clean)
    async with session.get(url, headers=_HEADERS, timeout=ClientTimeout(total=15)) as resp:
        resp.raise_for_status()
        data = await resp.json(content_type=None)

    if data.get("setStatus") != "OK":
        raise ValueError(f"Postcode lookup failed: {data.get('setMessage', 'unknown error')}")
    addresses = data.get("setData", [])
    if not addresses:
        raise ValueError(f"No addresses found for postcode {postcode}")
    return addresses


class SouthAndValeScraper(BaseScraper):
    NAME = "South Oxfordshire / Vale of White Horse"
    DESCRIPTION = "BinDays REST API — forms.southandvale.gov.uk"

    def __init__(self, session: ClientSession, uprn: str) -> None:
        self._session = session
        self._uprn = uprn
        self._url = BINDAYS_BINS_URL.format(uprn=uprn)

    async def fetch(self) -> list[Collection]:
        async with self._session.get(
            self._url,
            headers=_HEADERS,
            timeout=ClientTimeout(total=30),
        ) as resp:
            resp.raise_for_status()
            data = await resp.json(content_type=None)

        if data.get("setStatus") != "OK":
            raise ValueError(f"BinDays API error: {data.get('setMessage', 'unknown')}")

        today = dt_util.now().date()
        collections: list[Collection] = []

        for week in data.get("setData", {}).get("week", []):
            for day in week.get("day", []):
                event_date = _parse_date(day.get("collection_date", ""))
                if event_date is None or event_date < today:
                    continue

                raw_status = day.get("CollectionStatus", "")
                date_changed = "DATE-CHANGED" in raw_status.upper()
                reason_raw = day.get("CollectionReason", "")
                change_reason = reason_raw.replace("Reason: ", "").strip() if date_changed else None

                for bin_info in day.get("bins", []):
                    bin_type = _normalize_waste_type(bin_info.get("bin_type", "Unknown"))
                    collections.append(Collection(
                        date=event_date,
                        waste_type=bin_type,
                        icon=_guess_icon(bin_type),
                        description=bin_info.get("bin_description", ""),
                        date_changed=date_changed,
                        change_reason=change_reason,
                    ))

        collections.sort(key=lambda c: (c.date, c.waste_type))
        _LOGGER.debug("Fetched %d upcoming collection items for UPRN %s", len(collections), self._uprn)
        return collections
