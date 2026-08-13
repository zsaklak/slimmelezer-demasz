#!/usr/bin/env python3
"""Ellenőrzi a repository Markdown-fájljainak helyi hivatkozásait."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).parents[1]
LINK_RE = re.compile(r"(?<!!)\[[^]]*]\(([^)]+)\)")


def main() -> int:
    """Jelzi a hiányzó relatív fájlhivatkozásokat."""
    errors: list[str] = []
    checked = 0
    for document in sorted(ROOT.rglob("*.md")):
        if any(part.startswith(".") and part != ".github" for part in document.parts):
            continue
        text = document.read_text(encoding="utf-8")
        for raw_target in LINK_RE.findall(text):
            target = raw_target.strip().split(maxsplit=1)[0].strip("<>")
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            path_text = unquote(target.split("#", 1)[0])
            if not path_text:
                continue
            checked += 1
            resolved = (document.parent / path_text).resolve()
            try:
                resolved.relative_to(ROOT.resolve())
            except ValueError:
                errors.append(
                    f"{document.relative_to(ROOT)}: repositoryn kívüli hivatkozás: {target}"
                )
                continue
            if not resolved.exists():
                errors.append(f"{document.relative_to(ROOT)}: hiányzó cél: {target}")

    print(f"Ellenőrzött relatív dokumentációs hivatkozások: {checked}")
    for error in errors:
        print(f"HIBA: {error}", file=sys.stderr)
    print("Eredmény: " + ("SIKERES" if not errors else "SIKERTELEN"))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
