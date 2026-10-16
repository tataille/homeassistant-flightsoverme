#!/usr/bin/env python3
"""Copy the Lovelace card runtime into the HACS-installed integration."""
from __future__ import annotations
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "www"
TARGET = ROOT / "custom_components" / "flights_over_me" / "www"
TARGET.mkdir(parents=True, exist_ok=True)
for name in ("avion-domicile-card.js", "aircraft-png-library.js"):
    shutil.copy2(SOURCE / name, TARGET / name)
shutil.copytree(SOURCE / "aircraft-png", TARGET / "aircraft-png", dirs_exist_ok=True)
print(f"Synchronized Lovelace assets to {TARGET.relative_to(ROOT)}")
