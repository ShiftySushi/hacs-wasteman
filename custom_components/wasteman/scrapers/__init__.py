"""Scraper base types for Wasteman."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date


@dataclass
class Collection:
    date: date
    waste_type: str
    icon: str | None = field(default=None)
    description: str = field(default="")
    date_changed: bool = field(default=False)
    change_reason: str | None = field(default=None)

    def days_until(self, today: date) -> int:
        """Return days until this collection from the supplied local date."""
        return (self.date - today).days


class BaseScraper(ABC):
    NAME: str = ""
    DESCRIPTION: str = ""

    @abstractmethod
    async def fetch(self) -> list[Collection]:
        """Return upcoming collections sorted by date."""
