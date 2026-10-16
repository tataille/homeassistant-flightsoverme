"""Fetch nearby aircraft from the public ADSB.lol API."""
from __future__ import annotations

import asyncio
import logging
import math
from datetime import timedelta
import time

from aiohttp import ClientError
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import API_BASE, DOMAIN, SCAN_INTERVAL_SECONDS

_LOGGER = logging.getLogger(__name__)


def _number(value):
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


class AircraftCoordinator(DataUpdateCoordinator):
    """Keep a sorted snapshot of aircraft around the configured home point."""

    def __init__(self, hass: HomeAssistant, latitude: float, longitude: float, radius_km: int):
        self.latitude = latitude
        self.longitude = longitude
        self.radius_km = radius_km
        # ADSB.lol's /dist/{radius} endpoint expects an integer nautical-mile radius.
        # Round up so the API query still covers the configured kilometer radius;
        # _distance_km applies the exact configured radius locally afterwards.
        self.radius_nm = math.ceil(radius_km / 1.852)
        self.session = async_get_clientsession(hass)
        self._metadata_cache: dict[str, tuple[float, dict]] = {}
        self._military_hexes: set[str] = set()
        self._military_cache_expires = 0.0
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=SCAN_INTERVAL_SECONDS),
        )

    async def _async_update_data(self):
        url = f"{API_BASE}/lat/{self.latitude}/lon/{self.longitude}/dist/{self.radius_nm}"
        try:
            async with self.session.get(url, timeout=15) as response:
                if response.status == 429:
                    raise UpdateFailed("Limite de requêtes ADSB.lol atteinte")
                response.raise_for_status()
                payload = await response.json(content_type=None)
        except (ClientError, TimeoutError, ValueError) as err:
            raise UpdateFailed(f"Impossible de récupérer les avions : {err}") from err

        military_hexes = await self._async_military_hexes()

        aircraft = []
        for raw in payload.get("aircraft", []):
            lat = _number(raw.get("lat"))
            lon = _number(raw.get("lon"))
            if lat is None or lon is None:
                continue
            distance_km = self._distance_km(lat, lon)
            if distance_km > self.radius_km:
                continue
            aircraft.append({
                "hex": raw.get("hex"),
                "flight": (raw.get("flight") or "").strip() or None,
                "registration": raw.get("r"),
                "type": raw.get("t"),
                "description": raw.get("desc"),
                "lat": lat,
                "lon": lon,
                "distance_km": round(distance_km, 1),
                "altitude_m": self._altitude_m(raw.get("alt_baro")),
                "altitude_ft": raw.get("alt_baro") if isinstance(raw.get("alt_baro"), (int, float)) else None,
                "ground_speed_kmh": self._speed_kmh(raw.get("gs")),
                "heading": _number(raw.get("track")) or _number(raw.get("nav_heading")),
                "vertical_rate_fpm": _number(raw.get("baro_rate")),
                "seen_seconds": _number(raw.get("seen")),
                "squawk": raw.get("squawk"),
                "category": raw.get("category"),
                "is_military": (raw.get("hex") or "").lower() in military_hexes,
                "on_ground": raw.get("alt_baro") == "ground",
                "source": raw.get("type"),
            })
        aircraft.sort(key=lambda item: item["distance_km"])
        if aircraft:
            now = time.monotonic()
            for item in aircraft:
                cache_key = f"{(item.get('hex') or '').lower()}:{(item.get('flight') or '').strip().upper()}"
                cached = self._metadata_cache.get(cache_key)
                if cached and cached[0] > now:
                    item.update(cached[1])
            # Enrich the four closest planes so the card can switch between
            # the featured aircraft and up to three nearby alternatives.
            await asyncio.gather(*(self._async_enrich_aircraft(item) for item in aircraft[:4]))
        return {"aircraft": aircraft, "count": len(aircraft)}

    async def _async_military_hexes(self) -> set[str]:
        """Return cached ICAO hex codes flagged as military by ADSB.lol."""
        now = time.monotonic()
        if now < self._military_cache_expires:
            return self._military_hexes
        try:
            async with self.session.get(f"{API_BASE}/mil", timeout=15) as response:
                if response.status == 429:
                    return self._military_hexes
                response.raise_for_status()
                payload = await response.json(content_type=None)
            self._military_hexes = {
                str(item.get("hex", "")).strip().lower()
                for item in payload.get("aircraft", [])
                if isinstance(item, dict) and item.get("hex")
            }
            self._military_cache_expires = now + 600
        except (ClientError, TimeoutError, ValueError) as err:
            _LOGGER.debug("Optional military aircraft lookup failed: %s", err)
            # Retry sooner after an error while retaining the previous snapshot.
            self._military_cache_expires = now + 60
        return self._military_hexes

    async def _async_enrich_aircraft(self, aircraft: dict) -> None:
        """Add cached aircraft, airline, and best-effort route details."""
        now = time.monotonic()
        hex_code = (aircraft.get("hex") or "").lower()
        callsign = (aircraft.get("flight") or "").strip().upper()
        key = f"{hex_code}:{callsign}"
        cached = self._metadata_cache.get(key)
        if cached and cached[0] > now:
            aircraft.update(cached[1])
            return

        details = {}
        if hex_code and len(hex_code) == 6:
            result = await self._async_json(f"https://api.adsbdb.com/v0/aircraft/{hex_code}")
            info = (result or {}).get("response", {}).get("aircraft", {})
            if info:
                details.update({
                    "aircraft_type": info.get("type") or info.get("icao_type"),
                    "aircraft_icao_type": info.get("icao_type"),
                    "aircraft_manufacturer": info.get("manufacturer"),
                })

        prefix = callsign[:3]
        if prefix.isalpha():
            result = await self._async_json(f"https://api.adsbdb.com/v0/airline/{prefix}")
            airline_items = (result or {}).get("response", [])
            if airline_items:
                airline = airline_items[0]
                iata = airline.get("iata")
                details.update({
                    "airline_name": airline.get("name"),
                    "airline_icao": airline.get("icao"),
                    "airline_iata": iata,
                    "airline_country": airline.get("country"),
                    "airline_logo": f"https://images.kiwi.com/airlines/64/{iata}.png" if iata and iata.isalnum() else None,
                })

        # A route is not broadcast in ADS-B. ADSB.lol can infer one from the
        # callsign and current position; absence of a match is expected for
        # some private, charter, and unscheduled flights.
        if callsign and aircraft.get("lat") is not None and aircraft.get("lon") is not None:
            route = await self._async_route(callsign, aircraft["lat"], aircraft["lon"])
            details.update(self._route_details(route, callsign))

        aircraft.update(details)
        # Keep metadata for half an hour to avoid repeating lookups every poll.
        self._metadata_cache[key] = (now + 1800, details)

    async def _async_json(self, url: str):
        """Fetch optional enrichment data; a lookup failure is non-fatal."""
        try:
            async with self.session.get(url, timeout=8) as response:
                if response.status == 404:
                    return None
                if response.status == 429:
                    return None
                response.raise_for_status()
                return await response.json(content_type=None)
        except (ClientError, TimeoutError, ValueError) as err:
            _LOGGER.debug("Optional aircraft metadata lookup failed: %s", err)
            return None

    async def _async_route(self, callsign: str, lat: float, lon: float):
        """Look up a likely route using the aircraft's current location."""
        url = "https://api.adsb.lol/api/0/routeset"
        try:
            async with self.session.post(
                url,
                json={"planes": [{"callsign": callsign, "lat": lat, "lng": lon}]},
                timeout=8,
            ) as response:
                if response.status in (404, 429):
                    return None
                response.raise_for_status()
                return await response.json(content_type=None)
        except (ClientError, TimeoutError, ValueError) as err:
            _LOGGER.debug("Optional aircraft route lookup failed: %s", err)
            return None

    @staticmethod
    def _route_details(payload, callsign: str) -> dict:
        """Normalize ADSB.lol routeset results for the sensor and card."""
        if isinstance(payload, dict):
            candidates = payload.get("routes") or payload.get("planes") or [payload]
        elif isinstance(payload, list):
            candidates = payload
        else:
            return {}
        if not isinstance(candidates, list):
            return {}

        # Prefer the matching callsign, but tolerate endpoints that omit it.
        candidate = next(
            (item for item in candidates if isinstance(item, dict) and (item.get("callsign") or "").strip().upper() == callsign),
            next((item for item in candidates if isinstance(item, dict)), None),
        )
        if not candidate:
            return {}
        airports = candidate.get("_airports") or candidate.get("airports") or []
        if not isinstance(airports, list):
            airports = []

        def airport_value(airport, *keys):
            if not isinstance(airport, dict):
                return None
            return next((airport.get(key) for key in keys if airport.get(key)), None)

        origin = airports[0] if len(airports) >= 1 else {}
        destination = airports[-1] if len(airports) >= 2 else {}
        origin = origin if isinstance(origin, dict) else {}
        destination = destination if isinstance(destination, dict) else {}
        origin_iata = airport_value(origin, "iata")
        destination_iata = airport_value(destination, "iata")
        origin_icao = airport_value(origin, "icao")
        destination_icao = airport_value(destination, "icao")

        # Some responses carry only a route code string.
        codes = candidate.get("_airport_codes_iata") or candidate.get("airport_codes_iata") or candidate.get("airport_codes")
        if isinstance(codes, str) and "-" in codes:
            code_origin, code_destination = [part.strip() for part in codes.split("-", 1)]
            origin_iata = origin_iata or (code_origin if len(code_origin) == 3 else None)
            destination_iata = destination_iata or (code_destination if len(code_destination) == 3 else None)
            origin_icao = origin_icao or (code_origin if len(code_origin) == 4 else None)
            destination_icao = destination_icao or (code_destination if len(code_destination) == 4 else None)

        origin_city = airport_value(origin, "location", "municipality", "city")
        destination_city = airport_value(destination, "location", "municipality", "city")
        details = {
            "origin_city": origin_city or origin_iata or origin_icao,
            "destination_city": destination_city or destination_iata or destination_icao,
            "origin_airport": origin.get("name"),
            "destination_airport": destination.get("name"),
            "origin_iata": origin_iata,
            "destination_iata": destination_iata,
            "route_plausible": candidate.get("plausible"),
        }
        return {key: value for key, value in details.items() if value is not None}

    @staticmethod
    def _altitude_m(value):
        if not isinstance(value, (int, float)):
            return None
        return round(value * 0.3048)

    @staticmethod
    def _speed_kmh(value):
        number = _number(value)
        return round(number * 1.852) if number is not None else None

    def _distance_km(self, lat: float, lon: float) -> float:
        """Great-circle distance in km."""
        earth_km = 6371.0088
        lat1, lat2 = math.radians(self.latitude), math.radians(lat)
        delta_lat = lat2 - lat1
        delta_lon = math.radians(lon - self.longitude)
        a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2) ** 2
        return earth_km * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
