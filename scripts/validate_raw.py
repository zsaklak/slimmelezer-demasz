#!/usr/bin/env python3
"""Értékek kiírása nélkül ellenőrzi a Sagem MA309M Raw DSMR Telegramot."""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
import urllib.request
from pathlib import Path

DEFAULT_URL = "http://slimmelezer.local/text_sensor/raw_dsmr_telegram"
MAX_TELEGRAM_LENGTH = 1700

PARSER_PATH = (
    Path(__file__).parents[1] / "custom_components" / "slimmelezer_demasz" / "parser.py"
)


def load_parser_module():
    """Load the dependency-free integration parser without importing HA."""
    spec = importlib.util.spec_from_file_location(
        "slimmelezer_demasz_parser", PARSER_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"A parser nem tölthető be: {PARSER_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


ESPHOME_CODES = {
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

DOCUMENTED_HOME_ASSISTANT_CODES = {
    "0-0:42.0.0",
    "0-0:96.1.0",
    "0-0:98.1.0",
    "1-0:5.7.0",
    "1-0:5.8.0",
    "1-0:6.7.0",
    "1-0:6.8.0",
    "1-0:7.7.0",
    "1-0:7.8.0",
    "1-0:8.7.0",
    "1-0:8.8.0",
    "1-0:15.8.0",
}

EXPECTED_PROFILE_UNITS = (
    None,
    "kWh",
    "kWh",
    "kWh",
    "kWh",
    "kWh",
    "kWh",
    "kvarh",
    "kvarh",
    "kvarh",
    "kvarh",
    "kvarh",
    "kvarh",
    "kWh",
    "kW",
    "kW",
    "kW",
    "kW",
    "kW",
    "kW",
)


def load_telegram(url: str | None, input_path: Path | None) -> str:
    if input_path is not None:
        payload = json.loads(input_path.read_text(encoding="utf-8"))
    else:
        assert url is not None
        with urllib.request.urlopen(url, timeout=5) as response:
            payload = json.load(response)
    telegram = payload.get("value")
    if not isinstance(telegram, str):
        raise TypeError("A JSON-válasz nem tartalmaz szöveges 'value' mezőt.")
    return telegram


def profile_units(telegram: str) -> tuple[str | None, ...]:
    match = re.search(r"^0-0:98\.1\.0([^\r\n]*)", telegram, re.MULTILINE)
    if match is None:
        return ()
    groups = re.findall(r"\(([^)]*)\)", match.group(1))
    units: list[str | None] = []
    for group in groups:
        units.append(group.rsplit("*", 1)[1] if "*" in group else None)
    return tuple(units)


def main() -> int:
    parser = argparse.ArgumentParser()
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--url", default=DEFAULT_URL)
    source.add_argument("--input", type=Path)
    args = parser.parse_args()

    try:
        telegram = load_telegram(None if args.input else args.url, args.input)
    except (OSError, TypeError, ValueError) as exc:
        print(f"HIBA: a telegram nem olvasható: {exc}", file=sys.stderr)
        return 2

    observed = set(re.findall(r"^([0-9]+-[0-9]+:[0-9.]+)", telegram, re.MULTILINE))
    documented = ESPHOME_CODES | DOCUMENTED_HOME_ASSISTANT_CODES
    missing = sorted(documented - observed)
    units = profile_units(telegram)

    errors: list[str] = []
    warnings: list[str] = []
    if not telegram.startswith("/SAG5SAG-METER"):
        errors.append("nem a várt /SAG5SAG-METER fejléc érkezett")
    if re.search(r"![0-9A-Fa-f]{4}(?:\r\n)?$", telegram) is None:
        errors.append("hiányzik a ! + 4 hex alakú telegramvég")
    if len(telegram) > MAX_TELEGRAM_LENGTH:
        errors.append(
            f"a telegram {len(telegram)} karakter, nagyobb mint {MAX_TELEGRAM_LENGTH}"
        )
    elif len(telegram) > MAX_TELEGRAM_LENGTH - 100:
        warnings.append("100 karakternél kisebb tartalék maradt a telegrambufferben")
    try:
        parsed = load_parser_module().parse_telegram(telegram)
    except (RuntimeError, TypeError, ValueError) as exc:
        errors.append(
            f"a dinamikus HA-parser nem tudta feldolgozni a telegramot: {exc}"
        )
        parsed = None
    if units != EXPECTED_PROFILE_UNITS:
        errors.append(
            "a 0-0:98.1.0 profil nem a várt 20 csoportos egységsorrendet használja"
        )
    if parsed is not None and (
        parsed.power_import_kw is None or parsed.power_export_kw is None
    ):
        errors.append(
            "a hálózati nettó teljesítményhez szükséges import/export érték "
            "nem olvasható kW-ban"
        )
    if missing:
        warnings.append(
            "a pillanatnyi telegramból hiányzó dokumentált kódok: " + ", ".join(missing)
        )

    print(f"Telegramhossz: {len(telegram)}/{MAX_TELEGRAM_LENGTH}")
    print(f"Megfigyelt OBIS-kódok: {len(observed)}")
    print(f"ESPHome által lefedett kódok: {len(observed & ESPHOME_CODES)}")
    print(
        "HA-integráció dokumentált raw kódjai: "
        f"{len(observed & DOCUMENTED_HOME_ASSISTANT_CODES)}"
    )
    if parsed is not None:
        print(f"HA-integráció által képzett szenzorok: {len(parsed.registers)}")
        print(
            "Hálózati nettó teljesítmény alapadatai: "
            + (
                "rendben"
                if parsed.power_import_kw is not None
                and parsed.power_export_kw is not None
                else "hiányosak"
            )
        )
        print(f"Automatikusan felismert új OBIS-kódok: {len(parsed.unknown_codes)}")
    print(f"Profilcsoportok: {len(units)}")
    for warning in warnings:
        print(f"FIGYELMEZTETÉS: {warning}")
    for error in errors:
        print(f"HIBA: {error}", file=sys.stderr)
    print("Eredmény: " + ("SIKERES" if not errors else "SIKERTELEN"))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
