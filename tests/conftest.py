"""Minimal Home Assistant and aiohttp doubles for unit tests.

The production dependencies are supplied by Home Assistant. These doubles let
the pure parsing and calendar-boundary tests run in a clean Python environment;
they are not installed when the real packages are available.
"""
from __future__ import annotations

import importlib.util
import sys
from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from pathlib import Path
from types import ModuleType


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _add_module(name: str, *, package: bool = False) -> ModuleType:
    module = ModuleType(name)
    if package:
        module.__path__ = []
    sys.modules[name] = module
    return module


if importlib.util.find_spec("homeassistant") is None:
    homeassistant = _add_module("homeassistant", package=True)
    config_entries = _add_module("homeassistant.config_entries")
    core = _add_module("homeassistant.core")
    helpers = _add_module("homeassistant.helpers", package=True)
    aiohttp_client = _add_module("homeassistant.helpers.aiohttp_client")
    entity_platform = _add_module("homeassistant.helpers.entity_platform")
    update_coordinator = _add_module("homeassistant.helpers.update_coordinator")
    components = _add_module("homeassistant.components", package=True)
    calendar = _add_module("homeassistant.components.calendar")
    util = _add_module("homeassistant.util", package=True)
    dt_util = _add_module("homeassistant.util.dt")

    class ConfigEntry:  # pragma: no cover - import-only test double
        pass

    class HomeAssistant:  # pragma: no cover - import-only test double
        pass

    class DataUpdateCoordinator:  # pragma: no cover - import-only test double
        @classmethod
        def __class_getitem__(cls, _item):
            return cls

        def __init__(self, *_args, **_kwargs) -> None:
            pass

    class CoordinatorEntity:  # pragma: no cover - import-only test double
        @classmethod
        def __class_getitem__(cls, _item):
            return cls

        def __init__(self, coordinator) -> None:
            self.coordinator = coordinator

    class UpdateFailed(Exception):
        pass

    class CalendarEntity:  # pragma: no cover - import-only test double
        pass

    @dataclass
    class CalendarEvent:
        start: date | datetime
        end: date | datetime
        summary: str
        description: str | None = None

    config_entries.ConfigEntry = ConfigEntry
    core.HomeAssistant = HomeAssistant
    aiohttp_client.async_get_clientsession = lambda _hass: object()
    entity_platform.AddEntitiesCallback = object
    update_coordinator.DataUpdateCoordinator = DataUpdateCoordinator
    update_coordinator.CoordinatorEntity = CoordinatorEntity
    update_coordinator.UpdateFailed = UpdateFailed
    calendar.CalendarEntity = CalendarEntity
    calendar.CalendarEvent = CalendarEvent
    dt_util.now = lambda: datetime.now(timezone.utc)
    dt_util.start_of_local_day = lambda value: datetime.combine(
        value, time.min, tzinfo=timezone.utc
    )

    homeassistant.config_entries = config_entries
    homeassistant.core = core
    homeassistant.helpers = helpers
    homeassistant.components = components
    homeassistant.util = util
    helpers.aiohttp_client = aiohttp_client
    helpers.entity_platform = entity_platform
    helpers.update_coordinator = update_coordinator
    components.calendar = calendar
    util.dt = dt_util


if importlib.util.find_spec("aiohttp") is None:
    aiohttp = _add_module("aiohttp")

    class ClientSession:  # pragma: no cover - import-only test double
        pass

    class ClientTimeout:  # pragma: no cover - import-only test double
        def __init__(self, *, total: int) -> None:
            self.total = total

    aiohttp.ClientSession = ClientSession
    aiohttp.ClientTimeout = ClientTimeout
