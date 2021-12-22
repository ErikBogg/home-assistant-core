"""Config flow to configure the Luftdaten component."""
from __future__ import annotations

from typing import Any

from luftdaten import Luftdaten
from luftdaten.exceptions import LuftdatenConnectionError
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import (
    CONF_MONITORED_CONDITIONS,
    CONF_SCAN_INTERVAL,
    CONF_SENSORS,
    CONF_SHOW_ON_MAP,
)
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from .const import CONF_SENSOR_ID, DEFAULT_SCAN_INTERVAL, DOMAIN


class LuftDatenFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a Luftdaten config flow."""

    VERSION = 1

    @callback
    def _show_form(self, errors: dict[str, str] | None = None) -> FlowResult:
        """Show the form to the user."""
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_SENSOR_ID): cv.positive_int,
                    vol.Optional(CONF_SHOW_ON_MAP, default=False): bool,
                }
            ),
            errors=errors or {},
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the start of the config flow."""

        if not user_input:
            return self._show_form()

        await self.async_set_unique_id(str(user_input[CONF_SENSOR_ID]))
        self._abort_if_unique_id_configured()

        luftdaten = Luftdaten(user_input[CONF_SENSOR_ID])
        try:
            await luftdaten.get_data()
            valid = await luftdaten.validate_sensor()
        except LuftdatenConnectionError:
            return self._show_form({CONF_SENSOR_ID: "cannot_connect"})

        if not valid:
            return self._show_form({CONF_SENSOR_ID: "invalid_sensor"})

        available_sensors = [
            x for x, x_values in luftdaten.values.items() if x_values is not None
        ]

        if available_sensors:
            user_input.update(
                {CONF_SENSORS: {CONF_MONITORED_CONDITIONS: available_sensors}}
            )

        scan_interval = user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        user_input.update({CONF_SCAN_INTERVAL: scan_interval.total_seconds()})

        return self.async_create_entry(
            title=str(user_input[CONF_SENSOR_ID]), data=user_input
        )
