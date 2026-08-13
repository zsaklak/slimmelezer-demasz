"""Unit tests for the standalone DSMR parser."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

PARSER_PATH = (
    Path(__file__).parents[1] / "custom_components" / "slimmelezer_demasz" / "parser.py"
)
SPEC = importlib.util.spec_from_file_location("slimmelezer_demasz_parser", PARSER_PATH)
assert SPEC is not None and SPEC.loader is not None
parser = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = parser
SPEC.loader.exec_module(parser)


PROFILE_GROUPS = (
    "(260801000000S)"
    "(011495.026*kWh)(006180.893*kWh)(005314.133*kWh)"
    "(011814.522*kWh)(002964.902*kWh)(008849.620*kWh)"
    "(000014.362*kvarh)(009567.159*kvarh)"
    "(000007.093*kvarh)(000007.269*kvarh)"
    "(003105.453*kvarh)(006461.706*kvarh)"
    "(023309.548*kWh)"
    "(06.001*kW)(06.002*kW)(06.003*kW)"
    "(07.001*kW)(07.002*kW)(07.003*kW)"
)


def telegram(*lines: str) -> str:
    """Build a structurally valid fabricated telegram."""
    return "/SAG5SAG-METER\r\n\r\n" + "\r\n".join(lines) + "\r\n!ABCD\r\n"


class ParserTests(unittest.TestCase):
    def test_known_fields_and_profile_create_31_sensors(self) -> None:
        raw = telegram(
            "0-0:1.0.0(260811120000S)",
            "0-0:42.0.0(53414735)",
            "0-0:96.1.0(303132333435)",
            "1-0:5.7.0(00.001*kvar)",
            "1-0:6.7.0(00.002*kvar)",
            "1-0:7.7.0(00.003*kvar)",
            "1-0:8.7.0(00.004*kvar)",
            "1-0:5.8.0(01.001*kvarh)",
            "1-0:6.8.0(01.002*kvarh)",
            "1-0:7.8.0(01.003*kvarh)",
            "1-0:8.8.0(01.004*kvarh)",
            "1-0:15.8.0(02.001*kWh)",
            f"0-0:98.1.0{PROFILE_GROUPS}",
        )
        data = parser.parse_telegram(raw)
        self.assertEqual(31, len(data.registers))
        self.assertEqual(frozenset(), data.unknown_codes)
        self.assertNotIn("0_0_1_0_0", data.registers)
        self.assertEqual("53414735", data.registers["0_0_42_0_0"].value)
        self.assertEqual("260801000000S", data.registers["0_0_98_1_0_timestamp"].value)

    def test_unknown_single_and_multi_group_registers_are_discovered(self) -> None:
        raw = telegram(
            "1-0:14.7.0(50.000*Hz)",
            "9-9:1.2.3(001.250*kW)(AUTO)",
        )
        data = parser.parse_telegram(raw)
        self.assertEqual({"1-0:14.7.0", "9-9:1.2.3"}, set(data.unknown_codes))
        self.assertEqual(3, len(data.registers))
        frequency = data.registers["1_0_14_7_0"]
        self.assertEqual(50.0, frequency.value)
        self.assertEqual("frequency", frequency.device_class)
        self.assertEqual("measurement", frequency.state_class)
        self.assertEqual("AUTO", data.registers["9_9_1_2_3_group_2"].value)

    def test_bidirectional_power_is_exposed_in_kw_without_duplication(self) -> None:
        raw = telegram(
            "1-0:1.7.0(250*W)",
            "1-0:2.7.0(0.750*kW)",
        )
        data = parser.parse_telegram(raw)
        self.assertEqual(0.25, data.power_import_kw)
        self.assertEqual(0.75, data.power_export_kw)
        self.assertEqual({}, data.registers)

    def test_bad_profile_group_count_is_rejected(self) -> None:
        with self.assertRaises(parser.TelegramParseError):
            parser.parse_telegram(telegram("0-0:98.1.0(260801000000S)(1*kWh)"))

    def test_missing_terminator_is_rejected(self) -> None:
        with self.assertRaises(parser.TelegramParseError):
            parser.parse_telegram("/SAG5SAG-METER\r\n1-0:1.7.0(1*kW)\r\n")


if __name__ == "__main__":
    unittest.main()
