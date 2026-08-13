"""Parse the verified Démász/Sagem MA309M DSMR telegram profile."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final

HEADER: Final = "/SAG5SAG-METER"
LINE_RE: Final = re.compile(
    r"^(?P<obis>[0-9]+-[0-9]+:[0-9]+(?:\.[0-9]+)+)(?P<groups>(?:\([^)]*\))+)$"
)
GROUP_RE: Final = re.compile(r"\(([^)]*)\)")
END_RE: Final = re.compile(r"![0-9A-Fa-f]{4}(?:\r?\n)?$")
NUMBER_RE: Final = re.compile(r"^[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)$")

# Ezeket már az ESPHome DSMR platform adja át a Home Assistantnak. A custom
# integration csak figyeli őket, de nem hoz létre belőlük második entitást.
ESPHOME_NATIVE_CODES: Final = frozenset(
    {
        "0-0:1.0.0",
        "0-0:17.0.0",
        "0-0:96.3.10",
        "0-0:96.13.0",
        "0-0:96.14.0",
        "1-0:1.7.0",
        "1-0:1.8.0",
        "1-0:1.8.1",
        "1-0:1.8.2",
        "1-0:1.8.3",
        "1-0:1.8.4",
        "1-0:2.7.0",
        "1-0:2.8.0",
        "1-0:2.8.1",
        "1-0:2.8.2",
        "1-0:2.8.3",
        "1-0:2.8.4",
        "1-0:3.8.0",
        "1-0:4.8.0",
        "1-0:13.7.0",
        "1-0:21.7.0",
        "1-0:22.7.0",
        "1-0:31.4.0",
        "1-0:31.7.0",
        "1-0:32.7.0",
        "1-0:33.7.0",
        "1-0:41.7.0",
        "1-0:42.7.0",
        "1-0:51.4.0",
        "1-0:51.7.0",
        "1-0:52.7.0",
        "1-0:53.7.0",
        "1-0:61.7.0",
        "1-0:62.7.0",
        "1-0:71.4.0",
        "1-0:71.7.0",
        "1-0:72.7.0",
        "1-0:73.7.0",
    }
)


@dataclass(frozen=True, slots=True)
class KnownRegister:
    """Known non-native register metadata."""

    name: str
    device_class: str | None = None
    state_class: str | None = None
    force_text: bool = False


KNOWN_REGISTERS: Final[Mapping[str, KnownRegister]] = MappingProxyType(
    {
        "0-0:42.0.0": KnownRegister("COSEM logikai készüléknév", force_text=True),
        "0-0:96.1.0": KnownRegister("Mérő gyári száma (hex)", force_text=True),
        "1-0:5.7.0": KnownRegister(
            "Meddő teljesítmény QI", "reactive_power", "measurement"
        ),
        "1-0:6.7.0": KnownRegister(
            "Meddő teljesítmény QII", "reactive_power", "measurement"
        ),
        "1-0:7.7.0": KnownRegister(
            "Meddő teljesítmény QIII", "reactive_power", "measurement"
        ),
        "1-0:8.7.0": KnownRegister(
            "Meddő teljesítmény QIV", "reactive_power", "measurement"
        ),
        "1-0:5.8.0": KnownRegister("Meddő energia QI", "reactive_energy", "total"),
        "1-0:6.8.0": KnownRegister("Meddő energia QII", "reactive_energy", "total"),
        "1-0:7.8.0": KnownRegister("Meddő energia QIII", "reactive_energy", "total"),
        "1-0:8.8.0": KnownRegister("Meddő energia QIV", "reactive_energy", "total"),
        "1-0:15.8.0": KnownRegister("Kombinált hatásos energia", "energy", "total"),
    }
)

PROFILE_CODE: Final = "0-0:98.1.0"
PROFILE_FIELDS: Final = (
    ("timestamp", "Előző hó végi időbélyeg", None, None),
    ("active_import_total", "Előző hó végi aktív import összesen", "energy", "total"),
    ("active_import_t1", "Előző hó végi aktív import tarifa 1", "energy", "total"),
    ("active_import_t2", "Előző hó végi aktív import tarifa 2", "energy", "total"),
    ("active_export_total", "Előző hó végi aktív export összesen", "energy", "total"),
    ("active_export_t1", "Előző hó végi aktív export tarifa 1", "energy", "total"),
    ("active_export_t2", "Előző hó végi aktív export tarifa 2", "energy", "total"),
    (
        "reactive_import_total",
        "Előző hó végi meddő import összesen",
        "reactive_energy",
        "total",
    ),
    (
        "reactive_export_total",
        "Előző hó végi meddő export összesen",
        "reactive_energy",
        "total",
    ),
    ("reactive_q1", "Előző hó végi meddő energia QI", "reactive_energy", "total"),
    ("reactive_q2", "Előző hó végi meddő energia QII", "reactive_energy", "total"),
    ("reactive_q3", "Előző hó végi meddő energia QIII", "reactive_energy", "total"),
    ("reactive_q4", "Előző hó végi meddő energia QIV", "reactive_energy", "total"),
    ("combined_active", "Előző hó végi kombinált hatásos energia", "energy", "total"),
    ("max_import_total", "Előző havi maximum import összesen", "power", "measurement"),
    ("max_import_t1", "Előző havi maximum import tarifa 1", "power", "measurement"),
    ("max_import_t2", "Előző havi maximum import tarifa 2", "power", "measurement"),
    ("max_export_total", "Előző havi maximum export összesen", "power", "measurement"),
    ("max_export_t1", "Előző havi maximum export tarifa 1", "power", "measurement"),
    ("max_export_t2", "Előző havi maximum export tarifa 2", "power", "measurement"),
)

UNIT_DEVICE_CLASS: Final = MappingProxyType(
    {
        "kWh": "energy",
        "Wh": "energy",
        "kvarh": "reactive_energy",
        "varh": "reactive_energy",
        "kW": "power",
        "W": "power",
        "kvar": "reactive_power",
        "var": "reactive_power",
        "V": "voltage",
        "A": "current",
        "Hz": "frequency",
        "%": "power_factor",
        "m3": "volume",
        "m³": "volume",
    }
)


class TelegramParseError(ValueError):
    """Raised when the endpoint does not return a complete DSMR telegram."""


@dataclass(frozen=True, slots=True)
class RegisterValue:
    """One Home Assistant entity candidate."""

    key: str
    obis: str
    group_index: int
    name: str
    value: float | str
    unit: str | None
    device_class: str | None
    state_class: str | None
    known: bool


@dataclass(frozen=True, slots=True)
class TelegramData:
    """Parsed telegram state."""

    header: str
    telegram_length: int
    obis_codes: frozenset[str]
    registers: Mapping[str, RegisterValue]
    unknown_codes: frozenset[str]
    power_import_kw: float | None
    power_export_kw: float | None


def slug_obis(obis: str) -> str:
    """Create a stable ASCII key from an OBIS code."""
    return re.sub(r"[^a-z0-9]+", "_", obis.lower()).strip("_")


def _split_value(
    group: str, *, force_text: bool = False
) -> tuple[float | str, str | None]:
    """Split a DSMR value group into a state and optional unit."""
    raw_value, separator, raw_unit = group.rpartition("*")
    if not separator:
        raw_value = group
        raw_unit = ""
    unit = raw_unit or None
    if not force_text and NUMBER_RE.fullmatch(raw_value):
        return float(raw_value), unit
    return raw_value, unit


def _generic_state_class(obis: str, device_class: str | None) -> str | None:
    """Assign conservative statistics metadata to automatically found values."""
    if device_class in {"energy", "reactive_energy", "volume"} and ".8." in obis:
        return "total_increasing"
    if device_class is not None:
        return "measurement"
    return None


def _power_in_kw(group: str) -> float | None:
    """Return a DSMR power value normalized to kW."""
    value, unit = _split_value(group)
    if not isinstance(value, float):
        return None
    if unit == "kW":
        return value
    if unit == "W":
        return value / 1000
    return None


def _parse_profile(groups: list[str]) -> list[RegisterValue]:
    if len(groups) != len(PROFILE_FIELDS):
        raise TelegramParseError(
            f"A {PROFILE_CODE} profil {len(groups)} csoportos, a várt érték 20."
        )
    parsed: list[RegisterValue] = []
    for index, (suffix, name, device_class, state_class) in enumerate(PROFILE_FIELDS):
        value, unit = _split_value(groups[index], force_text=index == 0)
        parsed.append(
            RegisterValue(
                key=f"{slug_obis(PROFILE_CODE)}_{suffix}",
                obis=PROFILE_CODE,
                group_index=index,
                name=name,
                value=value,
                unit=unit,
                device_class=device_class,
                state_class=state_class,
                known=True,
            )
        )
    return parsed


def parse_telegram(telegram: str) -> TelegramData:
    """Parse a complete raw telegram and generate entity candidates."""
    if not telegram.startswith(HEADER):
        raise TelegramParseError(f"Nem a várt {HEADER} fejléc érkezett.")
    if END_RE.search(telegram) is None:
        raise TelegramParseError("Hiányzik a ! + 4 hexadecimális telegramvég.")

    registers: dict[str, RegisterValue] = {}
    obis_codes: set[str] = set()
    unknown_codes: set[str] = set()
    occurrences: dict[str, int] = {}
    power_import_kw: float | None = None
    power_export_kw: float | None = None

    for raw_line in telegram.splitlines():
        match = LINE_RE.fullmatch(raw_line.strip())
        if match is None:
            continue
        obis = match.group("obis")
        groups = GROUP_RE.findall(match.group("groups"))
        obis_codes.add(obis)

        if groups and obis == "1-0:1.7.0":
            power_import_kw = _power_in_kw(groups[0])
        elif groups and obis == "1-0:2.7.0":
            power_export_kw = _power_in_kw(groups[0])

        if obis in ESPHOME_NATIVE_CODES:
            continue
        if obis == PROFILE_CODE:
            for item in _parse_profile(groups):
                registers[item.key] = item
            continue

        metadata = KNOWN_REGISTERS.get(obis)
        if metadata is None:
            unknown_codes.add(obis)
        occurrences[obis] = occurrences.get(obis, 0) + 1
        occurrence_suffix = (
            "" if occurrences[obis] == 1 else f"_occurrence_{occurrences[obis]}"
        )

        for index, group in enumerate(groups):
            group_suffix = "" if len(groups) == 1 else f"_group_{index + 1}"
            key = f"{slug_obis(obis)}{occurrence_suffix}{group_suffix}"
            force_text = metadata.force_text if metadata is not None else False
            value, unit = _split_value(group, force_text=force_text)
            device_class = (
                metadata.device_class
                if metadata is not None
                else UNIT_DEVICE_CLASS.get(unit)
            )
            state_class = (
                metadata.state_class
                if metadata is not None
                else _generic_state_class(obis, device_class)
            )
            base_name = metadata.name if metadata is not None else f"OBIS {obis}"
            name = (
                base_name if len(groups) == 1 else f"{base_name} – csoport {index + 1}"
            )
            registers[key] = RegisterValue(
                key=key,
                obis=obis,
                group_index=index,
                name=name,
                value=value,
                unit=unit,
                device_class=device_class,
                state_class=state_class,
                known=metadata is not None,
            )

    if not obis_codes:
        raise TelegramParseError(
            "A telegram nem tartalmaz feldolgozható OBIS-adatsort."
        )

    return TelegramData(
        header=telegram.splitlines()[0],
        telegram_length=len(telegram),
        obis_codes=frozenset(obis_codes),
        registers=MappingProxyType(registers),
        unknown_codes=frozenset(unknown_codes),
        power_import_kw=power_import_kw,
        power_export_kw=power_export_kw,
    )
