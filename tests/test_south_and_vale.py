"""South and Vale API client regression tests."""
from __future__ import annotations

import asyncio
from datetime import date, timedelta

from homeassistant.util import dt as dt_util

from custom_components.wasteman.scrapers import Collection
from custom_components.wasteman.scrapers.south_and_vale import (
    SouthAndValeScraper,
    _normalize_waste_type,
    _parse_date,
    lookup_addresses,
)


class _Response:
    def __init__(self, payload: dict) -> None:
        self._payload = payload

    async def __aenter__(self) -> _Response:
        return self

    async def __aexit__(self, *_args) -> None:
        return None

    def raise_for_status(self) -> None:
        return None

    async def json(self, *, content_type=None) -> dict:
        return self._payload


class _Session:
    def __init__(self, payload: dict) -> None:
        self.payload = payload
        self.requests: list[tuple[str, dict]] = []

    def get(self, url: str, **kwargs) -> _Response:
        self.requests.append((url, kwargs))
        return _Response(self.payload)


def test_waste_type_parsing_and_explicit_day_calculation() -> None:
    assert _normalize_waste_type(" garden waste subscribers ") == "Garden Waste"
    assert _parse_date("24/07/2026") == date(2026, 7, 24)
    assert _parse_date("not a date") is None
    assert Collection(date(2026, 7, 24), "Refuse").days_until(date(2026, 7, 21)) == 3


def test_lookup_addresses_uses_the_provided_session() -> None:
    session = _Session(
        {"setStatus": "OK", "setData": [{"uprn": "123", "address": "1 Test Road"}]}
    )

    addresses = asyncio.run(lookup_addresses(session, "ox1 1aa"))

    assert addresses == [{"uprn": "123", "address": "1 Test Road"}]
    assert session.requests[0][0].endswith("/OX11AA")


def test_fetch_uses_the_provided_session_and_keeps_future_collections() -> None:
    collection_day = dt_util.now().date() + timedelta(days=1)
    session = _Session(
        {
            "setStatus": "OK",
            "setData": {
                "week": [
                    {
                        "day": [
                            {
                                "collection_date": collection_day.strftime("%d/%m/%Y"),
                                "CollectionStatus": "DATE-CHANGED",
                                "CollectionReason": "Reason: Bank holiday",
                                "bins": [{"bin_type": "recycling", "bin_description": "Blue bin"}],
                            }
                        ]
                    }
                ]
            },
        }
    )

    collections = asyncio.run(SouthAndValeScraper(session, "123").fetch())

    assert [(item.date, item.waste_type) for item in collections] == [
        (collection_day, "Recycling")
    ]
    assert collections[0].change_reason == "Bank holiday"
    assert session.requests[0][0].endswith("/123")
