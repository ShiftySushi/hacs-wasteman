"""Constants for the Wasteman integration."""

DOMAIN = "wasteman"

# Council identifiers
COUNCIL_SOUTH_OXFORDSHIRE = "south_oxfordshire"
COUNCIL_VALE_OF_WHITE_HORSE = "vale_of_white_horse"

COUNCILS = {
    COUNCIL_SOUTH_OXFORDSHIRE: "South Oxfordshire District Council",
    COUNCIL_VALE_OF_WHITE_HORSE: "Vale of White Horse District Council",
}

# iCal feeds published by South & Vale councils via Google Calendar.
# Keys are (collection_day, variant). Day is lowercase weekday name.
# To update when the council changes their calendar IDs, replace the URL values here.
# Source: https://www.whitehorsedc.gov.uk/.../add-your-waste-calendar-to-google-calendar-or-ical/
SOUTH_AND_VALE_ICAL_URLS: dict[tuple[str, str], str] = {
    ("monday",    "v1"): "https://calendar.google.com/calendar/ical/fgv3d29e2fdnnt1ld7gq4vtqok%40group.calendar.google.com/public/basic.ics",
    ("tuesday",   "v1"): "https://calendar.google.com/calendar/ical/t9khic9tvlktqh81g36c4535mo%40group.calendar.google.com/public/basic.ics",
    ("wednesday", "v1"): "https://calendar.google.com/calendar/ical/ung0tkep28tljmucs66g51ioj0%40group.calendar.google.com/public/basic.ics",
    ("thursday",  "v1"): "https://calendar.google.com/calendar/ical/dnpekak7c19rba8kst7piaimpg%40group.calendar.google.com/public/basic.ics",
    ("friday",    "v1"): "https://calendar.google.com/calendar/ical/tu6dq7f61s8i90vnb96d5smjkg%40group.calendar.google.com/public/basic.ics",
    ("monday",    "v2"): "https://calendar.google.com/calendar/ical/qfnbte8aomgagtu3svvpkov00k%40group.calendar.google.com/public/basic.ics",
    ("tuesday",   "v2"): "https://calendar.google.com/calendar/ical/skuln7sb58hv2qq804b308tgfg%40group.calendar.google.com/public/basic.ics",
    ("wednesday", "v2"): "https://calendar.google.com/calendar/ical/sdenqai396e4ms9u3u1caucdbc%40group.calendar.google.com/public/basic.ics",
    ("thursday",  "v2"): "https://calendar.google.com/calendar/ical/mqattk1slu3ogulm4u3nv8ik1k%40group.calendar.google.com/public/basic.ics",
    ("friday",    "v2"): "https://calendar.google.com/calendar/ical/qdr1chksa3mcpedjimul6d8fa0%40group.calendar.google.com/public/basic.ics",
}

COLLECTION_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
CALENDAR_VARIANTS = ["V1", "V2"]

# Config entry keys
CONF_COUNCIL = "council"
CONF_COLLECTION_DAY = "collection_day"
CONF_CALENDAR_VARIANT = "calendar_variant"

# Options keys
CONF_DISPLAY_FORMAT = "display_format"
CONF_EXCLUDED_TYPES = "excluded_types"
CONF_TYPE_ALIASES = "type_aliases"
CONF_SENSOR_PER_TYPE = "sensor_per_type"
CONF_LOOKAHEAD_DAYS = "lookahead_days"

DISPLAY_FORMAT_DAYS = "days"
DISPLAY_FORMAT_DATE = "date"
DISPLAY_FORMAT_COMBINED = "combined"

DEFAULT_DISPLAY_FORMAT = DISPLAY_FORMAT_COMBINED
DEFAULT_LOOKAHEAD_DAYS = 30
DEFAULT_SENSOR_PER_TYPE = True
