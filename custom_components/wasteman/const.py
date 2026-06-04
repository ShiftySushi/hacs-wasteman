"""Constants for the Wasteman integration."""

DOMAIN = "wasteman"

# BinDays REST API (South Oxfordshire / Vale of White Horse).
# Update these URLs if the council migrates their API.
# Source: https://forms.southandvale.gov.uk/binday.eb
BINDAYS_BASE = "https://forms.southandvale.gov.uk"
BINDAYS_POSTCODE_URL = BINDAYS_BASE + "/api/property/postcode/{postcode}"
BINDAYS_BINS_URL = BINDAYS_BASE + "/api/property/bins/{uprn}"

# Config entry data keys
CONF_UPRN = "uprn"
CONF_POSTCODE = "postcode"

# Options keys
CONF_NEXT_BINS_TYPES = "next_bins_types"   # whitelist for Next Bins sensor + per-type sensors
CONF_TYPE_ALIASES = "type_aliases"
CONF_SENSOR_PER_TYPE = "sensor_per_type"
CONF_DISPLAY_FORMAT = "display_format"
CONF_LOOKAHEAD_DAYS = "lookahead_days"
CONF_SEPARATOR = "separator"

DISPLAY_FORMAT_DAYS = "days"
DISPLAY_FORMAT_DATE = "date"
DISPLAY_FORMAT_COMBINED = "combined"

DEFAULT_DISPLAY_FORMAT = DISPLAY_FORMAT_COMBINED
DEFAULT_LOOKAHEAD_DAYS = 30
DEFAULT_SENSOR_PER_TYPE = True
DEFAULT_SEPARATOR = ", "

# Standard kerbside bin types shown by default.
# These are the four types most residents care about.
# Bulky Waste is excluded because it requires separate booking.
DEFAULT_NEXT_BINS_TYPES = ["Food Waste", "Garden Waste", "Recycling", "Refuse"]
