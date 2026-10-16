"""Aircraft summary sensors."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.const import EntityCategory

from .const import CONF_DISPLAY_MODE, CONF_RADIUS_KM, DEFAULT_DISPLAY_MODE, DOMAIN


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([NearestAircraftSensor(coordinator, entry)])


class NearestAircraftSensor(CoordinatorEntity, SensorEntity):
    """Expose nearest aircraft as a sensor with display attributes."""

    _attr_has_entity_name = True
    _attr_name = "Avion le plus proche"
    _attr_icon = "mdi:airplane"

    def __init__(self, coordinator, entry: ConfigEntry):
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_nearest_aircraft"
        self._attr_extra_state_attributes = {}
        self._radius_km = entry.data[CONF_RADIUS_KM]
        self._display_mode = entry.data.get(CONF_DISPLAY_MODE, DEFAULT_DISPLAY_MODE)

    @property
    def native_value(self):
        aircraft = self.coordinator.data.get("aircraft", []) if self.coordinator.data else []
        if not aircraft:
            return "Aucun avion détecté"
        return aircraft[0]["flight"] or aircraft[0]["registration"] or aircraft[0]["hex"] or "Avion détecté"

    @property
    def extra_state_attributes(self):
        aircraft = self.coordinator.data.get("aircraft", []) if self.coordinator.data else []
        nearest = aircraft[0] if aircraft else None
        return {
            "aircraft": aircraft,
            "nearest": nearest,
            "aircraft_count": len(aircraft),
            "radius_km": self._radius_km,
            "display_mode": self._display_mode,
            "home_latitude": self.coordinator.latitude,
            "home_longitude": self.coordinator.longitude,
            "data_source": "ADSB.lol",
        }
