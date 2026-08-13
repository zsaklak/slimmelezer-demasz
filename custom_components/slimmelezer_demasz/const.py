"""Constants for the SlimmeLezer Démász integration."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "slimmelezer_demasz"
PLATFORMS = ["sensor"]

CONF_RESOURCE_URL = "resource_url"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_GITHUB_AUTO_REPORT = "github_auto_report"
CONF_GITHUB_TOKEN = "github_token"
CONF_POWER_IMPORT_ENTITY = "power_import_entity"
CONF_POWER_EXPORT_ENTITY = "power_export_entity"

DEFAULT_RESOURCE_URL = "http://slimmelezer.local/text_sensor/raw_dsmr_telegram"
DEFAULT_SCAN_INTERVAL = 10
MIN_SCAN_INTERVAL = 5
DEFAULT_TIMEOUT = 5
DEFAULT_GITHUB_AUTO_REPORT = False

GITHUB_REPOSITORY = "zsaklak/slimmelezer-demasz"
GITHUB_ISSUES_URL = f"https://github.com/{GITHUB_REPOSITORY}/issues"
GITHUB_ISSUES_API_URL = f"https://api.github.com/repos/{GITHUB_REPOSITORY}/issues"
GITHUB_API_VERSION = "2026-03-10"
EVENT_NEW_OBIS = f"{DOMAIN}_new_obis"

MANUFACTURER = "Sagem"
MODEL = "MA309M + SlimmeLezer"


def update_interval(seconds: int) -> timedelta:
    """Return a coordinator update interval."""
    return timedelta(seconds=max(MIN_SCAN_INTERVAL, seconds))
