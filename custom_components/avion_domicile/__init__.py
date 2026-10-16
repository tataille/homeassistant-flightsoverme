"""Track nearby aircraft using the Home Assistant home location."""
from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import CONF_RADIUS_KM, DOMAIN, SCAN_INTERVAL_SECONDS
from .coordinator import AircraftCoordinator

PLATFORMS = [Platform.SENSOR]
_LOGGER = logging.getLogger(__name__)
FRONTEND_URL = f"/{DOMAIN}/static"


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Register the bundled Lovelace card and dashboard strategy."""
    static_dir = Path(__file__).parent / "www"
    await hass.http.async_register_static_paths(
        [StaticPathConfig(FRONTEND_URL, str(static_dir), cache_headers=False)]
    )
    add_extra_js_url(hass, f"{FRONTEND_URL}/avion-domicile-card.js")
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a configured instance."""
    lat = hass.config.latitude
    lon = hass.config.longitude
    if lat is None or lon is None:
        return False
    coordinator = AircraftCoordinator(
        hass,
        latitude=lat,
        longitude=lon,
        radius_km=entry.data[CONF_RADIUS_KM],
    )
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload an instance."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
