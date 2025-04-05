"""Tests for the FoxESS Cloud integration setup."""
from unittest.mock import patch, MagicMock

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

# Import constants and exceptions
from custom_components.foxess.const import DOMAIN, CONF_API_KEY, CONF_DEVICE_SN, PLATFORMS
from custom_components.foxess.api import FoxEssApiClient, FoxEssApiException

# Mock data matching config entry and API responses
MOCK_CONFIG_DATA = {
    CONF_API_KEY: "test-api-key",
    CONF_DEVICE_SN: "TEST_SN_INIT",
}

MOCK_DEVICE_DETAIL_SUCCESS = {
    "deviceSN": "TEST_SN_INIT",
    "plantName": "Init Test Plant",
    "deviceType": "H1-3.7-E",
    "masterVersion": "2.0",
    "slaveVersion": "2.1",
    "managerVersion": "2.2",
    "hasBattery": False,
    "status": 1,
}

MOCK_RAW_DATA_SUCCESS = {
    "datas": { # Assuming API nests data under 'datas'
        "pv1Power": 100.0,
        "SoC": 50.0,
        # Add other keys expected by sensors if needed for initial setup checks
    }
}


@pytest.fixture(autouse=True)
def mock_platforms():
    """Mock platforms loaded by the integration."""
    with patch(f"custom_components.{DOMAIN}.PLATFORMS", return_value=PLATFORMS):
        yield


async def test_async_setup_entry_success(hass: HomeAssistant) -> None:
    """Test successful setup of the integration."""
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG_DATA, entry_id="test-init-success")
    entry.add_to_hass(hass)

    # Patch the API client methods
    with patch(
        "custom_components.foxess.FoxEssApiClient", autospec=True
    ) as mock_api_client_class:
        # Configure the mock instance returned by the constructor
        mock_api_instance = mock_api_client_class.return_value
        mock_api_instance.get_device_detail.return_value = MOCK_DEVICE_DETAIL_SUCCESS
        # Mock the first data fetch done by coordinator's first refresh
        mock_api_instance.get_raw_data.return_value = MOCK_RAW_DATA_SUCCESS
        # Mock other calls that might happen in _async_update_data during first refresh
        mock_api_instance.get_battery_settings.return_value = {} # No battery in mock data
        mock_api_instance.get_report.return_value = {}

        # Setup the component
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    # Assertions
    assert entry.state == ConfigEntryState.LOADED
    assert DOMAIN in hass.data
    assert entry.entry_id in hass.data[DOMAIN]
    assert mock_api_client_class.call_count == 1 # API Client initialized
    assert mock_api_instance.get_device_detail.call_count >= 1 # Called during setup
    assert mock_api_instance.get_raw_data.call_count >= 1 # Called during coordinator refresh

    # Check device registry
    device_registry = dr.async_get(hass)
    device = device_registry.async_get_device(identifiers={(DOMAIN, MOCK_CONFIG_DATA[CONF_DEVICE_SN])})
    assert device is not None
    assert device.name == MOCK_DEVICE_DETAIL_SUCCESS["plantName"]
    assert device.manufacturer == "FoxESS"
    assert device.model == MOCK_DEVICE_DETAIL_SUCCESS["deviceType"]
    assert device.sw_version is not None # Check format if needed

    # Check that platforms were forwarded (implicitly checked by state being LOADED)
    # Check coordinator data (optional, depends on what needs verification)
    coordinator = hass.data[DOMAIN][entry.entry_id].get("coordinator")
    assert coordinator is not None
    assert coordinator.last_update_success is True
    assert coordinator.data is not None
    assert coordinator.data.get("online") is True # Should be online after successful raw data fetch


async def test_async_setup_entry_api_fail(hass: HomeAssistant) -> None:
    """Test integration setup failure if initial API call fails."""
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG_DATA, entry_id="test-init-fail")
    entry.add_to_hass(hass)

    # Patch the API client to raise an exception during initial get_device_detail
    with patch(
        "custom_components.foxess.FoxEssApiClient", autospec=True
    ) as mock_api_client_class:
        mock_api_instance = mock_api_client_class.return_value
        mock_api_instance.get_device_detail.side_effect = FoxEssApiException("API Connection Error")

        # Attempt setup
        assert not await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    # Assertions
    assert entry.state == ConfigEntryState.SETUP_ERROR
    assert entry.entry_id not in hass.data.get(DOMAIN, {}) # No data should be stored


async def test_async_unload_entry(hass: HomeAssistant) -> None:
    """Test successful unloading of the integration."""
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG_DATA, entry_id="test-unload")
    entry.add_to_hass(hass)

    # Setup successfully first
    with patch(
        "custom_components.foxess.FoxEssApiClient", autospec=True
    ) as mock_api_client_class:
        mock_api_instance = mock_api_client_class.return_value
        mock_api_instance.get_device_detail.return_value = MOCK_DEVICE_DETAIL_SUCCESS
        mock_api_instance.get_raw_data.return_value = MOCK_RAW_DATA_SUCCESS
        mock_api_instance.get_battery_settings.return_value = {}
        mock_api_instance.get_report.return_value = {}

        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert entry.state == ConfigEntryState.LOADED
    assert entry.entry_id in hass.data[DOMAIN]

    # Unload the entry
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    # Assertions
    assert entry.state == ConfigEntryState.NOT_LOADED
    assert entry.entry_id not in hass.data[DOMAIN]