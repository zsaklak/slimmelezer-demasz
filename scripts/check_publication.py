#!/usr/bin/env python3
"""Ellenőrzi a GitHub- és HACS-publikáció helyi előfeltételeit."""

from __future__ import annotations

import json
import os
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).parents[1]
DOMAIN = "slimmelezer_demasz"
REPOSITORY_URL = "https://github.com/zsaklak/slimmelezer-demasz"
REQUIRED_MANIFEST_KEYS = {
    "domain",
    "name",
    "codeowners",
    "config_flow",
    "documentation",
    "integration_type",
    "iot_class",
    "issue_tracker",
    "requirements",
    "version",
}
REQUIRED_FILES = {
    "LICENSE",
    "README.md",
    "hacs.json",
    "custom_components/slimmelezer_demasz/manifest.json",
    "custom_components/slimmelezer_demasz/config_flow.py",
    "custom_components/slimmelezer_demasz/reporting.py",
    "custom_components/slimmelezer_demasz/strings.json",
    "custom_components/slimmelezer_demasz/translations/hu.json",
    "esphome/slimmelezer_demasz.yaml",
    "docs/OBIS_MATRIX.md",
    "docs/ESPHOME.md",
    "docs/HACS.md",
    ".github/workflows/validate.yml",
    ".github/ISSUE_TEMPLATE/unknown_obis.yml",
}
PRIVATE_IPV4_RE = re.compile(
    r"\b(?:10(?:\.\d{1,3}){3}|192\.168(?:\.\d{1,3}){2}|"
    r"172\.(?:1[6-9]|2\d|3[01])(?:\.\d{1,3}){2})\b"
)
IGNORED_DIRECTORIES = {
    ".git",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
}


def main() -> int:
    """Ellenőrizze a publikálható repository-szerkezetet."""
    errors: list[str] = []

    for relative in sorted(REQUIRED_FILES):
        if not (ROOT / relative).is_file():
            errors.append(f"hiányzó kötelező fájl: {relative}")

    integrations = sorted(
        path.name for path in (ROOT / "custom_components").iterdir() if path.is_dir()
    )
    if integrations != [DOMAIN]:
        errors.append(
            "a custom_components pontosan egy slimmelezer_demasz integrációt tartalmazhat"
        )

    manifest = json.loads(
        (ROOT / "custom_components" / DOMAIN / "manifest.json").read_text(
            encoding="utf-8"
        )
    )
    missing_manifest = sorted(REQUIRED_MANIFEST_KEYS - manifest.keys())
    if missing_manifest:
        errors.append("hiányzó manifest-mezők: " + ", ".join(missing_manifest))
    if manifest.get("domain") != DOMAIN:
        errors.append("hibás manifest domain")
    if not manifest.get("codeowners"):
        errors.append("a manifest codeowners mezője üres")
    if manifest.get("documentation") != REPOSITORY_URL:
        errors.append("a manifest dokumentációs címe nem a tervezett repository")
    if manifest.get("issue_tracker") != f"{REPOSITORY_URL}/issues":
        errors.append("a manifest hibajegycíme nem a tervezett repository")

    hacs = json.loads((ROOT / "hacs.json").read_text(encoding="utf-8"))
    if hacs.get("name") != "SlimmeLezer Démász":
        errors.append("hibás HACS-megjelenítési név")
    if hacs.get("country") != "HU":
        errors.append("a magyar HACS country: HU beállítás hiányzik")

    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    if project["project"]["version"] != manifest.get("version"):
        errors.append("a pyproject és a manifest verziója eltér")

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    required_readme_text = (
        "A HACS a `custom_components/slimmelezer_demasz` integrációt telepíti",
        "active_energy_import_maximum_demand_last_13_months",
        "Kiválasztott nettó teljesítmény",
        f"{REPOSITORY_URL}/blob/main/esphome/slimmelezer_demasz.yaml",
        "Más MVM-területeken",
        "Issues: write",
    )
    for text in required_readme_text:
        if text not in readme:
            errors.append(f"a magyar HACS/README leírásból hiányzik: {text}")

    for forbidden in (ROOT / "esphome" / "secrets.yaml", ROOT / ".DS_Store"):
        if forbidden.exists():
            errors.append(f"nem publikálható helyi fájl: {forbidden.relative_to(ROOT)}")

    forbidden_public_markers = {
        "docker-claw": "belső gépnév",
        "tail8b03b": "belső tailnetnév",
        "/config/.codex-backups/": "belső mentési útvonal",
        "peterzsak.slimmelezer_demasz": "személyhez kötött ESPHome-projektazonosító",
    }

    for current, directories, filenames in os.walk(ROOT):
        directories[:] = [
            name for name in directories if name not in IGNORED_DIRECTORIES
        ]
        for filename in filenames:
            path = Path(current) / filename
            if path == Path(__file__):
                continue
            if path.suffix.lower() not in {
                ".md",
                ".json",
                ".py",
                ".toml",
                ".yaml",
                ".yml",
            }:
                continue
            content = path.read_text(encoding="utf-8")
            if PRIVATE_IPV4_RE.search(content):
                errors.append(f"belső IPv4-cím található: {path.relative_to(ROOT)}")
            for marker, description in forbidden_public_markers.items():
                if marker in content:
                    errors.append(
                        f"{description} található: {path.relative_to(ROOT)} ({marker})"
                    )

    print(f"Integrációk a repositoryban: {len(integrations)}")
    print(f"Kötelező fájlok: {len(REQUIRED_FILES)}")
    print(f"Manifest-mezők: {len(manifest)}")
    for error in errors:
        print(f"HIBA: {error}", file=sys.stderr)
    print("Eredmény: " + ("SIKERES" if not errors else "SIKERTELEN"))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
