"""The FoxESS Cloud integration."""
import asyncio
import logging
from datetime import timedelta, datetime

import async_timeout
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import FoxEssApiClient, FoxEssApiException, FoxEssApiAuthError, FoxEssApiTimeoutError, FoxEssApiResponseError
from .const import (
    API_CLIENT,
    CONF_API_KEY,
    CONF_DEVICE_SN,
    COORDINATOR,
    DEVICE_INFO_DATA,
    DOMAIN,
    PLATFORMS,
    SCAN_INTERVAL_MINUTES,
)

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
    hass.data[DOMAIN][entry.entry_id] = {
        DEVICE_INFO_DATA: device_info_data
    }

    # Create Device Registry Entry
    device_registry = hass.helpers.device_registry.async_get(hass)
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
        now = datetime.utcnow() # Use UTC for comparisons

        try:
            # --- Fetch Raw Data (Every Update) ---
            async with async_timeout.timeout(DEFAULT_TIMEOUT - 5): # Slightly less than total timeout
                raw_data = await api_client.get_raw_data()
                data["raw"] = raw_data.get("datas", {}) # API nests data under 'datas' key
                data["online"] = True # Mark as online if raw data fetch succeeds
                data["last_update_raw"] = now
                _LOGGER.debug("Successfully fetched raw data for %s", device_sn)

            # --- Fetch Device Detail (Periodically) ---
            last_detail_update = data["last_update_detail"]
            if last_detail_update is None or (now - last_detail_update > DEVICE_DETAIL_INTERVAL):
                 async with async_timeout.timeout(DEFAULT_TIMEOUT - 5):
                     device_detail = await api_client.get_device_detail()
                     data["device_detail"] = device_detail
                     hass.data[DOMAIN][entry.entry_id][DEVICE_INFO_DATA] = device_detail # Update stored info
                     data["last_update_detail"] = now
                     hass.data[DOMAIN][entry.entry_id]["last_update_detail"] = now
                     _LOGGER.debug("Successfully fetched device detail for %s", device_sn)

            # --- Fetch Battery Settings (Periodically) ---
            # Only fetch if device detail indicates a battery exists
            has_battery = bool(data["device_detail"].get("hasBattery")) # Check if key exists and is truthy
            last_battery_update = data["last_update_battery"]
            if has_battery and (last_battery_update is None or (now - last_battery_update > BATTERY_SETTINGS_INTERVAL)):
                 async with async_timeout.timeout(DEFAULT_TIMEOUT - 5):
                     battery_settings = await api_client.get_battery_settings()
                     data["battery"] = battery_settings
                     data["last_update_battery"] = now
                     hass.data[DOMAIN][entry.entry_id]["last_update_battery"] = now
                     _LOGGER.debug("Successfully fetched battery settings for %s", device_sn)

            # --- Fetch Reports (Periodically) ---
            last_report_update = data["last_update_report"]
            if last_report_update is None or (now - last_report_update > REPORT_INTERVAL):
                 async with async_timeout.timeout(DEFAULT_TIMEOUT - 5):
                     report_data = await api_client.get_report()
                     data["report"] = report_data # Structure depends on API response
                     # daily_gen_data = await api_client.get_report_daily_generation() # Uncomment if needed
                     # data["report_daily"] = daily_gen_data
                     data["last_update_report"] = now
                     hass.data[DOMAIN][entry.entry_id]["last_update_report"] = now
                     _LOGGER.debug("Successfully fetched report data for %s", device_sn)

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

    # --- Forward Setup to Platforms ---
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok