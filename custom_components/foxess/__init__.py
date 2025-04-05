"""The FoxESS Cloud integration."""
import asyncio
import logging
from datetime import timedelta, datetime
import time # Added for coordinator update logic

import async_timeout
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed # Added
# Removed duplicate import

from .api import FoxEssApiClient, FoxEssApiException, FoxEssApiAuthError, FoxEssApiTimeoutError, FoxEssApiResponseError, DEFAULT_TIMEOUT
from .const import (
    API_CLIENT,
    CONF_API_KEY,
    CONF_DEVICE_SN,
    CONF_EXTPV, # Added CONF_EXTPV import
    COORDINATOR,
    DEVICE_INFO_DATA,
    DOMAIN,
    PLATFORMS,
    SCAN_INTERVAL_MINUTES,
)

# Constants for coordinator update logic (adapted from old sensor.py)
RETRY_NEXT_SLOT = -1

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(minutes=SCAN_INTERVAL_MINUTES)

# Define intervals for less frequent updates
DEVICE_DETAIL_INTERVAL = timedelta(minutes=15)
BATTERY_SETTINGS_INTERVAL = timedelta(minutes=60)
REPORT_INTERVAL = timedelta(minutes=60)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up FoxESS Cloud from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    api_key = entry.data[CONF_API_KEY]
    device_sn = entry.data[CONF_DEVICE_SN]

    session = async_get_clientsession(hass)
    api_client = FoxEssApiClient(session, api_key, device_sn)

    # Fetch initial device info for registration
    try:
        async with async_timeout.timeout(30): # Shorter timeout for initial setup
             device_info_data = await api_client.get_device_detail()
    except (FoxEssApiException, asyncio.TimeoutError) as err:
        _LOGGER.error("Could not connect to FoxESS API during setup for %s: %s", device_sn, err)
        # Optionally: raise ConfigEntryNotReady(f"Could not connect: {err}")
        return False # Abort setup if initial connection fails

    # Store device info data for entities
    # Store api_client and device info for other platforms (like sensor) to access
    hass.data[DOMAIN][entry.entry_id] = {
        API_CLIENT: api_client,
        DEVICE_INFO_DATA: device_info_data,
        # COORDINATOR will likely be added by sensor.py when it sets up the coordinator
    }

    # Device registry creation moved after coordinator setup and refresh

    # --- Coordinator Setup ---
    async def _async_update_data():
        """Fetch data from API endpoint.

        This is the place to fetch data from your API service. Be sure to catch all errors
        and exceptions that may occur during data retrieval. Return the processed data.
        """
        data = {
            "raw": {},
            "battery": {},
            "report": {},
            "report_daily": {},
            "device_detail": hass.data[DOMAIN][entry.entry_id].get(DEVICE_INFO_DATA, {}), # Start with initial data
            "online": False, # Assume offline until successful raw data fetch
            "last_update_raw": None,
            "last_update_detail": hass.data[DOMAIN][entry.entry_id].get("last_update_detail"),
            "last_update_battery": hass.data[DOMAIN][entry.entry_id].get("last_update_battery"),
            "last_update_report": hass.data[DOMAIN][entry.entry_id].get("last_update_report"),
        }
        # Use local time for report index calculation, consistent with old code
        now_local = datetime.now()
        current_time = datetime.utcnow() # Keep using UTC for interval comparisons
        try:
            # Get extendPV option
            extend_pv = entry.options.get(CONF_EXTPV, False)

            # --- Fetch Raw Data (Every Update) ---
            async with async_timeout.timeout(DEFAULT_TIMEOUT - 5): # Slightly less than total timeout
                # Pass extend_pv option to get_raw_data
                raw_data_result = await api_client.get_raw_data(extend_pv=extend_pv)
                # Assuming get_raw_data returns the processed dictionary directly now
                data["raw"] = raw_data_result # Store the processed data
                data["online"] = True # Mark as online if raw data fetch succeeds
                data["last_update_raw"] = current_time # Use consistent time variable
                _LOGGER.debug("Successfully fetched raw data for %s", device_sn)

            # --- Fetch Device Detail (Periodically) ---
            last_detail_update = data["last_update_detail"]
            if last_detail_update is None or (current_time - last_detail_update > DEVICE_DETAIL_INTERVAL):
                 async with async_timeout.timeout(DEFAULT_TIMEOUT - 5):
                     device_detail = await api_client.get_device_detail()
                     data["device_detail"] = device_detail
                     hass.data[DOMAIN][entry.entry_id][DEVICE_INFO_DATA] = device_detail # Update stored info
                     data["last_update_detail"] = current_time
                     hass.data[DOMAIN][entry.entry_id]["last_update_detail"] = current_time
                     _LOGGER.debug("Successfully fetched device detail for %s", device_sn)

            # --- Fetch Battery Settings (Periodically) ---
            # Only fetch if device detail indicates a battery exists
            has_battery = bool(data["device_detail"].get("hasBattery")) # Check if key exists and is truthy
            last_battery_update = data["last_update_battery"]
            if has_battery and (last_battery_update is None or (current_time - last_battery_update > BATTERY_SETTINGS_INTERVAL)):
                 async with async_timeout.timeout(DEFAULT_TIMEOUT - 5):
                     battery_settings = await api_client.get_battery_settings()
                     data["battery"] = battery_settings
                     data["last_update_battery"] = current_time
                     hass.data[DOMAIN][entry.entry_id]["last_update_battery"] = current_time
                     _LOGGER.debug("Successfully fetched battery settings for %s", device_sn)

            # --- Fetch Reports (Periodically) ---
            last_report_update = data["last_update_report"]
            if last_report_update is None or (current_time - last_report_update > REPORT_INTERVAL):
                 async with async_timeout.timeout(DEFAULT_TIMEOUT - 5):
                     report_result = await api_client.get_report()
                     # Process the report to extract today's values (matches old code logic)
                     processed_report = {}
                     today_index = now_local.day - 1 # 0-based index for today
                     for item in report_result:
                         variable = item.get("variable")
                         values = item.get("values")
                         if variable and values and isinstance(values, list) and len(values) > today_index:
                             today_value = values[today_index]
                             processed_report[variable] = round(today_value, 3) if today_value is not None else 0
                         else:
                             processed_report[variable] = 0 # Default if data missing
                     data["report"] = processed_report # Store processed data for today
                     # daily_gen_data = await api_client.get_report_daily_generation() # Keep commented for now
                     # data["report_daily"] = daily_gen_data
                     data["last_update_report"] = current_time
                     hass.data[DOMAIN][entry.entry_id]["last_update_report"] = current_time
                     _LOGGER.debug("Successfully fetched and processed report data for %s", device_sn)

            _LOGGER.debug("Coordinator update successful for %s. Online: %s", device_sn, data["online"])
            return data

        except FoxEssApiAuthError as err:
            # Raising ConfigEntryAuthFailed will cancel future updates
            # and start a reauth flow.
            _LOGGER.error("Authentication error connecting to FoxESS API for %s: %s", device_sn, err)
            # Re-authentication might involve updating the API key via UI flow
            # For now, just log and fail update. Re-auth flow needs config_flow changes.
            # raise ConfigEntryAuthFailed from err
            raise UpdateFailed(f"Authentication error: {err}") from err
        except FoxEssApiTimeoutError as err:
            _LOGGER.warning("Timeout connecting to FoxESS API for %s: %s", device_sn, err)
            raise UpdateFailed(f"Timeout error: {err}") from err
        except FoxEssApiResponseError as err:
            _LOGGER.warning("Invalid response from FoxESS API for %s: %s", device_sn, err)
            raise UpdateFailed(f"Invalid response error: {err}") from err
        except FoxEssApiException as err:
            _LOGGER.error("Unknown API error connecting to FoxESS API for %s: %s", device_sn, err)
            raise UpdateFailed(f"Unknown API error: {err}") from err
        except asyncio.TimeoutError as err:
             _LOGGER.warning("Coordinator update timed out for %s: %s", device_sn, err)
             raise UpdateFailed(f"Coordinator update timed out: {err}") from err


    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"{DOMAIN}_{device_sn}",
        update_method=_async_update_data,
        update_interval=SCAN_INTERVAL,
    )

    # Store coordinator and API client
    hass.data[DOMAIN][entry.entry_id].update({
        COORDINATOR: coordinator,
        API_CLIENT: api_client,
    })

    # --- Initial Refresh ---
    await coordinator.async_config_entry_first_refresh()
    # --- Create Device Registry Entry (Moved Here) ---
    device_registry = hass.helpers.device_registry.async_get()
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, device_sn)},
        name=device_info_data.get("plantName", f"FoxESS {device_sn}"), # Use plantName if available
        manufacturer="FoxESS",
        model=device_info_data.get("deviceType", "Unknown"),
        sw_version=f"Master: {device_info_data.get('masterVersion', 'N/A')}, "
                   f"Slave: {device_info_data.get('slaveVersion', 'N/A')}, "
                   f"Manager: {device_info_data.get('managerVersion', 'N/A')}",
        # hw_version can be added if available from API
    )

    # --- Forward Setup to Platforms ---
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Add listener for options updates
    entry.async_on_unload(entry.add_update_listener(update_listener))

    return True


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    _LOGGER.debug("Options updated: %s", entry.options)
    # Reload the integration to apply changes
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok