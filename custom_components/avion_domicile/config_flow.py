"""Configuration flow for Avion au-dessus du domicile."""
from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import SelectSelector, SelectSelectorConfig

from .const import (
    CONF_DISPLAY_MODE,
    CONF_RADIUS_KM,
    DEFAULT_DISPLAY_MODE,
    DEFAULT_RADIUS_KM,
    DOMAIN,
    MAX_RADIUS_KM,
    MODE_HOUSE,
    MODE_RADAR,
)

class AvionDomicileConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Set up the integration using Home Assistant's configured location."""

    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        errors = {}
        if user_input is not None:
            if self.hass.config.latitude is None or self.hass.config.longitude is None:
                errors["base"] = "location_not_configured"
            else:
                await self.async_set_unique_id(DOMAIN)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title="Avion au-dessus du domicile",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user", data_schema=self._schema(), errors=errors
        )

    async def async_step_reconfigure(self, user_input=None) -> FlowResult:
        """Allow changing the display mode and search radius later."""
        entry = self._get_reconfigure_entry()
        if user_input is not None:
            await self.async_set_unique_id(entry.unique_id)
            self._abort_if_unique_id_mismatch()
            return self.async_update_reload_and_abort(entry, data_updates=user_input)

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self._schema(entry.data),
        )

    @staticmethod
    def _schema(current=None):
        """Build the setup form, retaining existing values on reconfigure."""
        current = current or {}
        return vol.Schema(
            {
                vol.Required(
                    CONF_DISPLAY_MODE,
                    default=current.get(CONF_DISPLAY_MODE, DEFAULT_DISPLAY_MODE),
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=[MODE_HOUSE, MODE_RADAR],
                        translation_key=CONF_DISPLAY_MODE,
                    )
                ),
                vol.Required(
                    CONF_RADIUS_KM,
                    default=current.get(CONF_RADIUS_KM, DEFAULT_RADIUS_KM),
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=MAX_RADIUS_KM)),
            }
        )
