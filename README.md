# Wasteman

A lightweight [Home Assistant](https://www.home-assistant.io/) integration for waste collection schedules in **South Oxfordshire** and **Vale of White Horse** districts.

Wasteman uses the councils' BinDays service to look up an address by postcode and retrieve its upcoming collections.

## Requirements

- Home Assistant 2024.1.0 or later
- [HACS](https://hacs.xyz/)

## Installation

1. In HACS, go to **Integrations** → **⋮** → **Custom repositories**
2. Add `https://github.com/ShiftySushi/hacs-wasteman` as an **Integration**
3. Install **Wasteman** from the HACS store
4. Restart Home Assistant
5. Go to **Settings → Devices & Services → Add Integration** and search for **Wasteman**

## Setup

During setup you will be asked for:

| Field | Description |
|---|---|
| **Postcode** | Your full UK postcode, used to find eligible addresses |
| **Address** | Select the address whose collection schedule you want to track |

## Customisation

After setup, open the integration's **Configure** option to adjust:

- **Display format** — `in 3 days`, `Wednesday 4 Jun 2025`, or both (default)
- **Individual sensors** — additionally create one sensor for each selected waste type (default: enabled); the aggregate **Next Bins** sensor is always created
- **Lookahead window** — how many days ahead to include in the `upcoming` attribute (default: 30)
- **Bins to show** — choose the waste types shown by the aggregate sensor and calendar
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
| State | `Blue Bin, Brown Bin - 3 days` |
| `upcoming` | `[{"date": "...", "days_until": 3, "waste_types": ["Blue Bin", "Brown Bin"]}, ...]` |

### Calendar

A `calendar.waste_collections` entity compatible with the Lovelace calendar card. Respects the selected bin types and aliases.

## Updating after a council website change

If South & Vale migrate their BinDays service, update the endpoint constants in `custom_components/wasteman/const.py`. The response parsing in `custom_components/wasteman/scrapers/south_and_vale.py` may also need to change if their JSON format changes.

## Adding new councils

Supporting another council requires a scraper for its collection service, plus corresponding coordinator and config-flow changes. The current integration supports South Oxfordshire and Vale of White Horse only.
