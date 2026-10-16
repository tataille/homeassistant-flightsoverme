#!/usr/bin/env python3
"""Create a Home Assistant release archive with the expected folder layout."""
from __future__ import annotations
import json, sys, zipfile
from pathlib import Path
root = Path(__file__).resolve().parents[1]
tag = sys.argv[1]
version = json.loads((root / "custom_components/avion_domicile/manifest.json").read_text())["version"]
if tag.removeprefix("v") != version:
    raise SystemExit(f"Tag {tag} does not match manifest version {version}")
output = root / f"avion-domicile-ha-{version}.zip"
include = [root / "custom_components/avion_domicile", root / "www", root / "README.md", root / "hacs.json", root / "LICENSE"]
with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED, compresslevel=8) as archive:
    for item in include:
        if item.is_file():
            archive.write(item, item.relative_to(root))
        else:
            for path in sorted(item.rglob("*")):
                if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
                    archive.write(path, path.relative_to(root))
with zipfile.ZipFile(output) as archive:
    if archive.testzip() is not None:
        raise SystemExit("Created archive failed ZIP integrity check")
print(output)
