# Wasteman

A lightweight [Home Assistant](https://www.home-assistant.io/) integration for waste collection schedules in **South Oxfordshire** and **Vale of White Horse** districts.

Uses the official Google Calendar iCal feeds published by South & Vale councils — the most stable interface available, since updating a calendar ID in one file is all it takes to fix things if the council changes their website.

## Requirements

- Home Assistant 2024.1.0 or later
- [HACS](https://hacs.xyz/)

## Installation

1. In HACS, go to **Integrations** → **⋮** → **Custom repositories**
2. Add `https://github.com/<your-username>/hacs-wasteman` as an **Integration**
3. Install **Wasteman** from the HACS store
4. Restart Home Assistant
5. Go to **Settings → Devices & Services → Add Integration** and search for **Wasteman**

## Setup

During setup you will be asked for:

| Field | Description |
|---|---|
| **Council** | South Oxfordshire or Vale of White Horse |
| **Collection day** | The weekday your bins are collected (Monday–Friday) |
| **Calendar variant** | V1 or V2 — check the [South & Vale website](https://www.whitehorsedc.gov.uk/vale-of-white-horse-district-council/recycling-rubbish-and-waste/when-is-your-collection-day/waste-collections-calendar/add-your-waste-calendar-to-google-calendar-or-ical/) to find which applies to your street |

## Customisation

After setup, open the integration's **Configure** option to adjust:

- **Display format** — `in 3 days`, `Wednesday 4 Jun 2025`, or both (default)
- **Sensor mode** — one sensor per waste type (default) or a single aggregate sensor
- **Lookahead window** — how many days ahead to include in the `upcoming` attribute (default: 30)
- **Excluded types** — hide waste types you don't want tracked (e.g. `Garden waste`)
- **Aliases** — rename waste types to friendlier labels, one per line:
  ```
  Recycling and food waste = Blue Bin
  Rubbish = Black Bin
  Garden waste = Brown Bin
  ```

## Entities

### Sensors (per-type mode)

One sensor per waste type, e.g. `sensor.recycling_and_food_waste`.

| Attribute | Example |
|---|---|
| State | `Wednesday 4 Jun 2025 (in 3 days)` |
| `upcoming` | `[{"date": "2025-06-04", "days_until": 3}, ...]` |

### Sensor (aggregate mode)

Single sensor `sensor.next_collection`.

| Attribute | Example |
|---|---|
| State | `Blue Bin: Wednesday 4 Jun 2025 (in 3 days)` |
| `upcoming` | `[{"date": "...", "days_until": 3, "waste_type": "Blue Bin"}, ...]` |

### Calendar

A `calendar.waste_collections` entity compatible with the Lovelace calendar card. Respects excluded types and aliases.

## Updating after a council website change

If South & Vale change their Google Calendar IDs, edit `custom_components/wasteman/const.py` and update the affected URL(s) in `SOUTH_AND_VALE_ICAL_URLS`. No other changes are required.

## Adding new councils

1. Add a new class inheriting `BaseScraper` in `custom_components/wasteman/scrapers/`
2. Register it in `coordinator._build_scraper()`
3. Add the council to `const.COUNCILS` and extend the config flow in `config_flow.py`
