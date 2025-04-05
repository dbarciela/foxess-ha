"""Config flow for FoxESS Cloud integration."""
import logging
import voluptuous as vol

from homeassistant import config_entries
# Removed import from homeassistant.const, will import from .const below
from homeassistant.core import callback

from .const import DOMAIN, CONF_DEVICE_SN, CONF_API_KEY # Added CONF_API_KEY

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_KEY): str,
        vol.Required(CONF_DEVICE_SN): str,
    }
)


class FoxESSConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for FoxESS Cloud."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            # TODO: Add validation here to test API key and SN if possible
            # For now, assume valid input
            await self.async_set_unique_id(user_input[CONF_DEVICE_SN])
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=f"FoxESS Inverter {user_input[CONF_DEVICE_SN]}", data=user_input
            )

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )

    # TODO: Add async_step_reauth if API key changes require re-authentication