"""Config flow for FoxESS Cloud integration."""
import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME # Needed for title, though not configurable here
from homeassistant.core import callback
from homeassistant.helpers import selector
from .const import DOMAIN, CONF_DEVICE_SN, CONF_API_KEY, CONF_EXTPV, CONF_DEVICE_ID # Added CONF_DEVICE_ID
from .const import DOMAIN, CONF_DEVICE_SN, CONF_API_KEY, CONF_EXTPV # Added CONF_EXTPV

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

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> FoxESSOptionsFlowHandler:
        """Get the options flow for this handler."""
        return FoxESSOptionsFlowHandler(config_entry)


class FoxESSOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle FoxESS options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict | None = None) -> config_entries.FlowResult:
        """Manage the options."""
        if user_input is not None:
            # Update the config entry's options
            return self.async_create_entry(title="", data=user_input)

        # Get current options or defaults
        extend_pv = self.config_entry.options.get(CONF_EXTPV, False)

        options_schema = vol.Schema(
            {
                vol.Optional(CONF_EXTPV, default=extend_pv): selector.BooleanSelector(),
            }
        )

        return self.async_show_form(step_id="init", data_schema=options_schema)

    async def async_step_import(self, import_data: dict | None = None) -> config_entries.FlowResult:
        """Handle import from configuration.yaml."""
        _LOGGER.debug("Importing FoxESS config from configuration.yaml: %s", import_data)

        # Extract required data from YAML import
        api_key = import_data.get(CONF_API_KEY)
        device_sn = import_data.get(CONF_DEVICE_SN)
        # Use legacy deviceID for unique_id to preserve history
        legacy_device_id = import_data.get(CONF_DEVICE_ID, device_sn) # Fallback to SN if ID missing

        if not api_key or not device_sn:
             _LOGGER.error("Import failed: Missing apiKey or deviceSN in YAML config.")
             # Cannot proceed without these
             # Returning abort might be better if HA handles this gracefully
             return self.async_abort(reason="import_missing_data")

        await self.async_set_unique_id(legacy_device_id)
        self._abort_if_unique_id_configured(updates={
             CONF_API_KEY: api_key,
             CONF_DEVICE_SN: device_sn,
             # Don't store legacy deviceID in data, only use for unique_id
        })

        # Extract options from YAML if they exist
        options = {}
        if CONF_EXTPV in import_data:
            options[CONF_EXTPV] = import_data[CONF_EXTPV]

        # Create entry using legacy_device_id as title for clarity during migration? Or use SN?
        # Using SN might be less confusing long-term.
        title = f"FoxESS Inverter {device_sn} (Imported)"

        return self.async_create_entry(
            title=title,
            data={
                CONF_API_KEY: api_key,
                CONF_DEVICE_SN: device_sn,
                # Do not store legacy deviceID here, unique_id handles it
            },
            options=options,
        )