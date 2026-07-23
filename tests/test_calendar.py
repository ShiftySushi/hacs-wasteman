"""Calendar regression tests."""
from __future__ import annotations

import asyncio
from datetime import date, datetime, timezone
from types import SimpleNamespace

from custom_components.wasteman.calendar import WastemanCalendar
from custom_components.wasteman.scrapers import Collection


def test_get_events_accepts_timezone_aware_bounds() -> None:
    """All-day collection events must be compared using local aware datetimes."""
    calendar = object.__new__(WastemanCalendar)
    calendar._entry = SimpleNamespace(options={})
    calendar.coordinator = SimpleNamespace(
        data=[Collection(date=date(2026, 7, 24), waste_type="Recycling")]
    )

    events = asyncio.run(
        calendar.async_get_events(
            None,
            datetime(2026, 7, 24, tzinfo=timezone.utc),
            datetime(2026, 7, 25, tzinfo=timezone.utc),
        )
    )

    assert [event.summary for event in events] == ["Recycling"]
    assert events[0].start == date(2026, 7, 24)
