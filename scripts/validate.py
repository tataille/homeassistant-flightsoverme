#!/usr/bin/env python3
"""Validate Home Assistant integration metadata and aircraft assets."""
from __future__ import annotations
import json, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components" / "avion_domicile"
manifest = json.loads((INTEGRATION / "manifest.json").read_text(encoding="utf-8"))
version = manifest.get("version", "")
if not re.fullmatch(r"\d+\.\d+\.\d+", version):
    raise SystemExit(f"Invalid integration version: {version!r}")
for path in [INTEGRATION / "strings.json", *sorted((INTEGRATION / "translations").glob("*.json")), ROOT / "hacs.json", ROOT / "release-please-config.json", ROOT / ".release-please-manifest.json", ROOT / "www" / "aircraft-png" / "catalog.json"]:
    json.loads(path.read_text(encoding="utf-8"))
catalog = json.loads((ROOT / "www" / "aircraft-png" / "catalog.json").read_text(encoding="utf-8"))
for aircraft in catalog:
    code = aircraft["code"]
    if not (ROOT / "www" / "aircraft-png" / f"{code}.png").is_file():
        raise SystemExit(f"Missing PNG for ICAO type {code}")
if "--tag" in sys.argv:
    tag = sys.argv[sys.argv.index("--tag") + 1]
    if tag.removeprefix("v") != version:
        raise SystemExit(f"Release tag {tag!r} does not match manifest version {version!r}")
print(f"Validated integration v{version} and {len(catalog)} aircraft illustrations")
