"""Tests for the FoxESS Cloud config flow."""
from unittest.mock import patch

import pytest
from homeassistant import config_entries, data_entry_flow
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_API_KEY

# Import constants and the config flow class
from custom_components.foxess.const import DOMAIN, CONF_DEVICE_SN
from custom_components.foxess.config_flow import FoxESSConfigFlow

# Import exceptions for potential future testing
# from custom_components.foxess.api import FoxEssApiAuthError, FoxEssApiException

# Pytest marker for all tests in this file
pytestmark = pytest.mark.usefixtures("mock_setup_entry") # Assumes a fixture to prevent component setup

# Mock data
MOCK_USER_INPUT = {
    CONF_API_KEY: "test-api-key",
    CONF_DEVICE_SN: "TEST_SN_123",
}

MOCK_DEVICE_INFO_SUCCESS = { # Mock data returned by get_device_detail
  "deviceSN": "TEST_SN_123",
  "plantName": "Mock Plant",
  "deviceType": "H1-5.0-E",
  "masterVersion": "1.0",
  "slaveVersion": "1.1",
  "managerVersion": "1.2",
  "hasBattery": True,
  "status": 1,
}


async def test_user_flow_success(hass: HomeAssistant) -> None:
    """Test the full user configuration flow successfully creates an entry."""
    # Start the config flow
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    # Check that the initial form is shown
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"
    assert result["errors"] is None

    # Simulate user input
    # Patch the API call that might happen during validation (none currently, but good practice)
    # with patch("custom_components.foxess.api.FoxEssApiClient.get_device_detail", return_value=MOCK_DEVICE_INFO_SUCCESS):
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=MOCK_USER_INPUT,
    )
    await hass.async_block_till_done() # Allow tasks to complete

    # Check that the flow finished and created an entry
    assert result2["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result2["title"] == f"FoxESS Inverter {MOCK_USER_INPUT[CONF_DEVICE_SN]}"
    assert result2["data"] == MOCK_USER_INPUT
    assert result2["result"].unique_id == MOCK_USER_INPUT[CONF_DEVICE_SN]


async def test_user_flow_already_configured(hass: HomeAssistant, mock_config_entry) -> None:
    """Test the flow aborts if the device SN is already configured."""
    # Setup an existing entry with the same SN
    mock_config_entry.add_to_hass(hass)

    # Start the config flow
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    # Simulate user input with the same SN
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=MOCK_USER_INPUT, # Assumes MOCK_USER_INPUT SN matches mock_config_entry
    )

    # Check that the flow aborted
    assert result2["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result2["reason"] == "already_configured"


# Add more tests here for:
# - Handling API errors during validation (if validation is added to config flow)
#   - e.g., patch get_device_detail to raise FoxEssApiAuthError -> check for "invalid_auth" error
#   - e.g., patch get_device_detail to raise FoxEssApiException -> check for "cannot_connect" error
# - Re-authentication flow (async_step_reauth) if implemented