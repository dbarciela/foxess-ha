"""Tests for the FoxESS Cloud sensor platform."""
import json
from pathlib import Path
from unittest.mock import patch, AsyncMock

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry, load_fixture

from homeassistant.core import HomeAssistant
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.config_entries import ConfigEntryState

# Import constants and the domain
from custom_components.foxess.const import DOMAIN, CONF_API_KEY, CONF_DEVICE_SN
from custom_components.foxess.api import FoxEssApiClient # Needed for patching

# Reuse mock data from init tests or define specific ones
MOCK_CONFIG_DATA = {
    CONF_API_KEY: "test-api-key-sensor",
    CONF_DEVICE_SN: "TEST_SN_SENSOR",
}

# Load mock data from fixtures
DEVICE_DETAIL_SUCCESS = json.loads(load_fixture("device_detail_success.json"))
RAW_DATA_ONLINE = json.loads(load_fixture("raw_data_online.json"))
RAW_DATA_OFFLINE = json.loads(load_fixture("raw_data_offline.json"))
BATTERY_SETTINGS = json.loads(load_fixture("battery_settings_success.json"))
REPORT_DATA = json.loads(load_fixture("report_data_success.json"))

# Adjust fixture data SNs to match MOCK_CONFIG_DATA if necessary
DEVICE_DETAIL_SUCCESS["result"]["deviceSN"] = MOCK_CONFIG_DATA[CONF_DEVICE_SN]
RAW_DATA_ONLINE["result"]["sn"] = MOCK_CONFIG_DATA[CONF_DEVICE_SN]
RAW_DATA_OFFLINE["result"]["sn"] = MOCK_CONFIG_DATA[CONF_DEVICE_SN]
# Assume battery/report fixtures don't contain SN or it doesn't matter for the test


@pytest.fixture(autouse=True)
def mock_platforms_fixture():
    """Mock platforms loaded by the integration."""
    with patch(f"custom_components.{DOMAIN}.PLATFORMS", return_value=["sensor"]):
        yield


async def setup_integration(hass: HomeAssistant, config_data=MOCK_CONFIG_DATA) -> MockConfigEntry:
    """Set up the integration with patched API client."""
    entry = MockConfigEntry(domain=DOMAIN, data=config_data, entry_id="test-sensor-entry")
    entry.add_to_hass(hass)

    # Patch the API client constructor and methods
    with patch(
        "custom_components.foxess.FoxEssApiClient", autospec=True
    ) as mock_api_client_class:
        mock_api_instance = mock_api_client_class.return_value

        # Define behavior for the initial setup calls
        mock_api_instance.get_device_detail.return_value = DEVICE_DETAIL_SUCCESS["result"]
        mock_api_instance.get_raw_data.return_value = RAW_DATA_ONLINE["result"] # First update is online
        mock_api_instance.get_battery_settings.return_value = BATTERY_SETTINGS["result"]
        mock_api_instance.get_report.return_value = REPORT_DATA["result"]

        # Setup the component
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    # Store the mock instance for later use in tests if needed
    hass.data[f"{DOMAIN}_mock_api"] = mock_api_instance

    assert entry.state == ConfigEntryState.LOADED
    return entry


async def test_sensor_creation_and_initial_state(hass: HomeAssistant) -> None:
    """Test that sensors are created and have the correct initial state."""
    await setup_integration(hass)
    mock_api: AsyncMock = hass.data[f"{DOMAIN}_mock_api"] # Get the mock instance

    # --- Check Raw Data Sensors ---
    # Check a few key sensors based on RAW_DATA_ONLINE fixture
    pv1_power_state = hass.states.get(f"sensor.foxess_{MOCK_CONFIG_DATA[CONF_DEVICE_SN]}_pv1_power")
    assert pv1_power_state is not None
    assert pv1_power_state.state == "1234.5" # Value from raw_data_online.json
    assert pv1_power_state.attributes.get("unit_of_measurement") == "W"

    soc_state = hass.states.get(f"sensor.foxess_{MOCK_CONFIG_DATA[CONF_DEVICE_SN]}_battery_soc")
    assert soc_state is not None
    assert soc_state.state == "75.5"
    assert soc_state.attributes.get("unit_of_measurement") == "%"

    ambient_temp_state = hass.states.get(f"sensor.foxess_{MOCK_CONFIG_DATA[CONF_DEVICE_SN]}_ambient_temperature")
    assert ambient_temp_state is not None
    assert ambient_temp_state.state == "18.0"
    assert ambient_temp_state.attributes.get("unit_of_measurement") == "°C"

    # Check the custom status sensor
    status_state = hass.states.get(f"sensor.foxess_{MOCK_CONFIG_DATA[CONF_DEVICE_SN]}_inverter_status")
    assert status_state is not None
    assert status_state.state == "Normal" # Mapped from "1" in raw_data_online.json

    # --- Check Battery Setting Sensors ---
    # These rely on DEVICE_DETAIL_SUCCESS indicating hasBattery=true
    min_soc_grid_state = hass.states.get(f"sensor.foxess_{MOCK_CONFIG_DATA[CONF_DEVICE_SN]}_min_soc_on_grid")
    assert min_soc_grid_state is not None
    assert min_soc_grid_state.state == "20" # Value from battery_settings_success.json

    # --- Check Report Sensors ---
    # These rely on data from REPORT_DATA fixture
    gen_today_state = hass.states.get(f"sensor.foxess_{MOCK_CONFIG_DATA[CONF_DEVICE_SN]}_energy_generated_today")
    assert gen_today_state is not None
    assert gen_today_state.state == "15.5" # Value from report_data_success.json
    assert gen_today_state.attributes.get("unit_of_measurement") == "kWh"

    # --- Check Availability ---
    # All sensors checked above should be available because raw data was fetched successfully
    assert pv1_power_state.state != STATE_UNAVAILABLE
    assert soc_state.state != STATE_UNAVAILABLE
    assert status_state.state != STATE_UNAVAILABLE
    assert min_soc_grid_state.state != STATE_UNAVAILABLE
    assert gen_today_state.state != STATE_UNAVAILABLE


# Add more tests here for:
# - Coordinator updates with different data (e.g., offline raw data)
#   - Patch mock_api.get_raw_data.return_value = RAW_DATA_OFFLINE["result"]
#   - Trigger coordinator refresh: await coordinator.async_refresh()
#   - Assert sensor states become unavailable or show offline status
# - Handling missing keys in API responses
# - Sensors becoming available/unavailable based on battery presence changing
# - Attribute updates on the status sensor