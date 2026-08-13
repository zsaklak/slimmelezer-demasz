"""Tests for privacy-safe unknown OBIS reporting."""

from __future__ import annotations

from urllib.parse import parse_qs, urlparse

from custom_components.slimmelezer_demasz.parser import parse_telegram
from custom_components.slimmelezer_demasz.reporting import (
    build_obis_report,
    issue_body,
    issue_draft_url,
)


def test_report_contains_structure_but_never_raw_value() -> None:
    """Expose enough metadata for review without leaking the measurement."""
    data = parse_telegram(
        "/SAG5SAG-METER\r\n9-9:1.2.3(12345.678*mystery)(PRIVATE-TEXT)\r\n!ABCD\r\n"
    )
    report = build_obis_report(data, "9-9:1.2.3")
    body = issue_body(report)
    url = issue_draft_url(report)
    query = parse_qs(urlparse(url).query)

    assert report.group_count == 2
    assert report.units == ("mystery", "nincs")
    assert report.value_types == ("szám", "szöveg")
    assert "12345.678" not in body
    assert "PRIVATE-TEXT" not in body
    assert "12345.678" not in url
    assert "PRIVATE-TEXT" not in url
    assert query["template"] == ["unknown_obis.yml"]
    assert query["obis"] == ["9-9:1.2.3"]
