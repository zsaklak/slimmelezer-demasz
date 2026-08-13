"""Privacy-safe reporting for newly discovered OBIS registers."""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from dataclasses import asdict, dataclass
from types import MappingProxyType
from urllib.parse import urlencode

from aiohttp import ClientError
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.storage import Store

from .const import (
    CONF_GITHUB_AUTO_REPORT,
    CONF_GITHUB_TOKEN,
    DEFAULT_GITHUB_AUTO_REPORT,
    DEFAULT_TIMEOUT,
    DOMAIN,
    EVENT_NEW_OBIS,
    GITHUB_API_VERSION,
    GITHUB_ISSUES_API_URL,
    GITHUB_ISSUES_URL,
)
from .parser import TelegramData, slug_obis

LOGGER = logging.getLogger(__name__)
STORE_VERSION = 1


@dataclass(frozen=True, slots=True)
class ObisReport:
    """Value-free structural description of one unknown OBIS register."""

    obis: str
    group_count: int
    units: tuple[str, ...]
    value_types: tuple[str, ...]
    inferred_device_classes: tuple[str, ...]
    inferred_state_classes: tuple[str, ...]
    telegram_header: str

    @property
    def fingerprint(self) -> str:
        """Return a stable structural fingerprint without raw values."""
        payload = json.dumps(
            asdict(self), ensure_ascii=True, separators=(",", ":"), sort_keys=True
        )
        return hashlib.sha256(payload.encode()).hexdigest()[:16]


def build_obis_report(data: TelegramData, obis: str) -> ObisReport:
    """Build a privacy-safe report from parsed register metadata."""
    registers = sorted(
        (register for register in data.registers.values() if register.obis == obis),
        key=lambda register: (register.group_index, register.key),
    )
    if not registers:
        raise ValueError(f"Az OBIS-kódhoz nem tartozik raw regiszter: {obis}")

    return ObisReport(
        obis=obis,
        group_count=len(registers),
        units=tuple(register.unit or "nincs" for register in registers),
        value_types=tuple(
            "szám" if isinstance(register.value, float) else "szöveg"
            for register in registers
        ),
        inferred_device_classes=tuple(
            register.device_class or "nincs" for register in registers
        ),
        inferred_state_classes=tuple(
            register.state_class or "nincs" for register in registers
        ),
        telegram_header=data.header,
    )


def _joined(values: tuple[str, ...]) -> str:
    return ", ".join(values)


def issue_body(report: ObisReport) -> str:
    """Return a value-free GitHub issue body."""
    return "\n".join(
        (
            "## Automatikusan felismert OBIS-regiszter",
            "",
            f"- OBIS-kód: `{report.obis}`",
            f"- Értékcsoportok száma: {report.group_count}",
            f"- Mértékegységek: `{_joined(report.units)}`",
            f"- Értéktípusok: `{_joined(report.value_types)}`",
            (
                "- Kikövetkeztetett eszközosztályok: "
                f"`{_joined(report.inferred_device_classes)}`"
            ),
            (
                "- Kikövetkeztetett állapotosztályok: "
                f"`{_joined(report.inferred_state_classes)}`"
            ),
            f"- Telegramfejléc: `{report.telegram_header}`",
            f"- Szerkezeti ujjlenyomat: `{report.fingerprint}`",
            "",
            "## Ellenőrzési kérés",
            "",
            (
                "Kérjük ellenőrizni, hogy szabványos OBIS-regiszterről van-e szó, "
                "és szükséges-e dokumentált név, eszközosztály vagy állapotosztály "
                "felvétele az integrációba."
            ),
            "",
            (
                "> Ez a jelentés nem tartalmaz mérési értéket, mérőazonosítót, "
                "forrás-URL-t, hostnevet vagy IP-címet."
            ),
        )
    )


def issue_draft_url(report: ObisReport) -> str:
    """Return a prefilled GitHub issue form URL."""
    parameters = {
        "template": "unknown_obis.yml",
        "title": f"[Új OBIS]: {report.obis}",
        "obis": report.obis,
        "groups": str(report.group_count),
        "units": _joined(report.units),
        "value_types": _joined(report.value_types),
        "device_classes": _joined(report.inferred_device_classes),
        "state_classes": _joined(report.inferred_state_classes),
        "header": report.telegram_header,
        "fingerprint": report.fingerprint,
    }
    return f"{GITHUB_ISSUES_URL}/new?{urlencode(parameters)}"


def repair_issue_id(entry: ConfigEntry, obis: str) -> str:
    """Return a stable Repairs issue identifier per source and OBIS code."""
    return f"unknown_obis_{entry.entry_id}_{slug_obis(obis)}"


class UnknownObisReporter:
    """Create Repairs issues and optionally submit deduplicated GitHub issues."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self._store: Store[dict[str, dict[str, str]]] = Store(
            hass, STORE_VERSION, f"{DOMAIN}.reporting.{entry.entry_id}", private=True
        )
        self._reported: dict[str, str] = {}
        self._lock = asyncio.Lock()

    @property
    def automatic(self) -> bool:
        """Return whether automatic GitHub submission is enabled."""
        return bool(
            self.entry.options.get(CONF_GITHUB_AUTO_REPORT, DEFAULT_GITHUB_AUTO_REPORT)
        )

    @property
    def mode(self) -> str:
        """Return the non-secret reporting mode."""
        return "automatic" if self.automatic else "manual"

    @property
    def reported_count(self) -> int:
        """Return the number of successfully submitted fingerprints."""
        return len(self._reported)

    async def async_initialize(self) -> None:
        """Load successful report fingerprints from private storage."""
        stored = await self._store.async_load() or {}
        reported = stored.get("reported", {})
        if isinstance(reported, dict):
            self._reported = {str(key): str(value) for key, value in reported.items()}

    async def async_report_codes(
        self, data: TelegramData, obis_codes: list[str]
    ) -> None:
        """Report new unknown codes without ever including raw values."""
        async with self._lock:
            for obis in sorted(set(obis_codes)):
                report = build_obis_report(data, obis)
                draft_url = issue_draft_url(report)
                ir.async_create_issue(
                    self.hass,
                    DOMAIN,
                    repair_issue_id(self.entry, obis),
                    is_fixable=False,
                    is_persistent=True,
                    learn_more_url=draft_url,
                    severity=ir.IssueSeverity.WARNING,
                    translation_key="new_obis",
                    translation_placeholders={
                        "obis": report.obis,
                        "group_count": str(report.group_count),
                    },
                )
                event_data = MappingProxyType(
                    {
                        "obis": report.obis,
                        "group_count": report.group_count,
                        "units": list(report.units),
                        "value_types": list(report.value_types),
                        "device_classes": list(report.inferred_device_classes),
                        "state_classes": list(report.inferred_state_classes),
                        "fingerprint": report.fingerprint,
                        "issue_draft_url": draft_url,
                    }
                )
                self.hass.bus.async_fire(EVENT_NEW_OBIS, event_data)

                if not self.automatic or report.fingerprint in self._reported:
                    continue
                token = str(self.entry.options.get(CONF_GITHUB_TOKEN, "")).strip()
                if not token:
                    LOGGER.error(
                        "Az automatikus GitHub-jelentés aktív, de nincs token; "
                        "az OBIS-kód csak a Javítások között jelenik meg: %s",
                        report.obis,
                    )
                    continue
                issue_url = await self._async_submit(report, token)
                if issue_url is None:
                    continue
                self._reported[report.fingerprint] = issue_url
                await self._store.async_save({"reported": self._reported})

    async def _async_submit(self, report: ObisReport, token: str) -> str | None:
        """Submit one privacy-safe GitHub issue and return its public URL."""
        session = async_get_clientsession(self.hass)
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": GITHUB_API_VERSION,
        }
        payload = {
            "title": f"[Új OBIS]: {report.obis}",
            "body": issue_body(report),
        }
        try:
            async with asyncio.timeout(DEFAULT_TIMEOUT):
                response = await session.post(
                    GITHUB_ISSUES_API_URL, headers=headers, json=payload
                )
                response.raise_for_status()
                result = await response.json(content_type=None)
        except (TimeoutError, ClientError, ValueError) as err:
            LOGGER.error(
                "Az automatikus GitHub-jelentés sikertelen (%s): %s",
                report.obis,
                err,
            )
            return None

        issue_url = result.get("html_url") if isinstance(result, dict) else None
        if not isinstance(issue_url, str):
            LOGGER.error(
                "A GitHub sikeres válasza nem tartalmaz issue URL-t (%s)", report.obis
            )
            return None
        LOGGER.info("Az új OBIS-regiszter GitHub-jelentése elkészült: %s", issue_url)
        return issue_url
