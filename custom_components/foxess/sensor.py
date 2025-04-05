"""Sensor platform for FoxESS Cloud integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfReactivePower,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import COORDINATOR, DOMAIN, CONF_DEVICE_SN, DEVICE_INFO_DATA
from .api import FoxEssApiClient # Although not used directly here, good for context
from .definitions import SENSOR_DESCRIPTIONS, BATTERY_SETTING_SENSORS, REPORT_SENSORS

_LOGGER = logging.getLogger(__name__)

# (Definitions moved to definitions.py)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up FoxESS Cloud sensor entities based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id][COORDINATOR]
    device_info_data = hass.data[DOMAIN][entry.entry_id][DEVICE_INFO_DATA]
    device_sn = entry.data[CONF_DEVICE_SN]

    entities = []

    # Create entities from raw data descriptions
    for description in SENSOR_DESCRIPTIONS:
        # Check if the key exists in the first update's raw data
        # This prevents creating sensors for optional/missing values
        if description.key in coordinator.data.get("raw", {}):
             entities.append(FoxEssRawSensor(coordinator, description, device_sn))
        else:
             _LOGGER.debug("Skipping sensor %s for %s as key not found in initial data", description.key, device_sn)

    # Create entities from battery settings data
    has_battery = bool(device_info_data.get("hasBattery"))
    if has_battery:
        for description in BATTERY_SETTING_SENSORS:
             if description.key in coordinator.data.get("battery", {}):
                 entities.append(FoxEssBatterySettingSensor(coordinator, description, device_sn))
             else:
                 _LOGGER.debug("Skipping battery sensor %s for %s as key not found in initial data", description.key, device_sn)

    # Create entities from report data
    # Note: Report data structure might need adjustment based on API response
    # Assuming report data is a dict where keys match description.key and value is the energy total for today
    today_report_data = coordinator.data.get("report", {}).get("today", {}) # Example structure, adjust as needed
    for description in REPORT_SENSORS:
        if description.key in today_report_data:
             entities.append(FoxEssReportSensor(coordinator, description, device_sn))
        else:
             _LOGGER.debug("Skipping report sensor %s for %s as key not found in initial data", description.key, device_sn)


    # Add inverter status sensor (example of a custom entity)
    entities.append(FoxEssInverterStatusSensor(coordinator, device_sn))

    async_add_entities(entities)


class FoxEssEntity(CoordinatorEntity, SensorEntity):
    """Base class for FoxESS Cloud sensor entities."""

    _attr_has_entity_name = True # Use description.name as the entity name suffix

    def __init__(self, coordinator, description: SensorEntityDescription, device_sn: str):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._device_sn = device_sn
        self._attr_unique_id = f"{device_sn}_{description.key}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        # Fetch device details stored during __init__.py setup
        device_info_data = self.coordinator.hass.data[DOMAIN][self.coordinator.config_entry.entry_id][DEVICE_INFO_DATA]
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_sn)},
            name=device_info_data.get("plantName", f"FoxESS {self._device_sn}"),
            manufacturer="FoxESS",
            model=device_info_data.get("deviceType", "Unknown"),
            sw_version=f"Master: {device_info_data.get('masterVersion', 'N/A')}, "
                       f"Slave: {device_info_data.get('slaveVersion', 'N/A')}, "
                       f"Manager: {device_info_data.get('managerVersion', 'N/A')}",
        )

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        # Available if coordinator is updating and the specific data key exists
        return (
            super().available
            and self.coordinator.data is not None
            and self.coordinator.data.get("online", False) # Check if inverter reported online
        )

    def _get_data_value(self, data_key: str) -> Any | None:
        """Helper to get value from the correct part of coordinator data."""
        # Overridden by subclasses to specify where to look (raw, battery, report)
        raise NotImplementedError

    @property
    def native_value(self) -> float | str | None:
        """Return the state of the sensor."""
        value = self._get_data_value(self.entity_description.key)

        if value is None:
            return None

        # Attempt to convert to float if it's a numeric type sensor
        if self.entity_description.native_unit_of_measurement is not None and self.entity_description.device_class not in [SensorDeviceClass.ENUM, SensorDeviceClass.TIMESTAMP]: # Adjust as needed
             try:
                 return float(value)
             except (ValueError, TypeError):
                 _LOGGER.warning("Could not convert value '%s' to float for sensor %s", value, self.entity_id)
                 return None # Or return the raw value if appropriate
        return value # Return raw value for non-numeric types


class FoxEssRawSensor(FoxEssEntity):
    """Sensor reading data from the 'raw' part of the coordinator data."""
    def _get_data_value(self, data_key: str) -> Any | None:
        """Get value from the 'raw' data dictionary."""
        return self.coordinator.data.get("raw", {}).get(data_key)

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        # Check base availability and if the specific key exists in raw data
        return (
            super().available
            and self.coordinator.data.get("raw") is not None
            and self.entity_description.key in self.coordinator.data["raw"]
        )


class FoxEssBatterySettingSensor(FoxEssEntity):
    """Sensor reading data from the 'battery' part of the coordinator data."""
    def _get_data_value(self, data_key: str) -> Any | None:
        """Get value from the 'battery' data dictionary."""
        return self.coordinator.data.get("battery", {}).get(data_key)

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        # Check base availability and if the specific key exists in battery data
        return (
            super().available
            and self.coordinator.data.get("battery") is not None
            and self.entity_description.key in self.coordinator.data["battery"]
        )


class FoxEssReportSensor(FoxEssEntity):
    """Sensor reading data from the 'report' part of the coordinator data."""
    # This assumes the report data for 'today' is structured appropriately
    # Adjust the key access logic if the API response structure is different

    def _get_data_value(self, data_key: str) -> Any | None:
        """Get value from the 'report' data dictionary (assuming today's data)."""
        # Example: Accessing today's value for the specific key
        # Adjust ".get('today', {})" based on actual API response structure
        return self.coordinator.data.get("report", {}).get("today", {}).get(data_key)

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        # Check base availability and if the specific key exists in report data
        return (
            super().available
            and self.coordinator.data.get("report") is not None
            and self.coordinator.data["report"].get("today") is not None # Check if today's data exists
            and self.entity_description.key in self.coordinator.data["report"]["today"]
        )


# --- Example Custom Sensor (Not using EntityDescription) ---
class FoxEssInverterStatusSensor(CoordinatorEntity, SensorEntity):
    """Representation of the Inverter Status."""

    _attr_has_entity_name = True
    _attr_name = "Inverter Status"
    _attr_icon = "mdi:solar-power" # Or mdi:information-outline

    def __init__(self, coordinator, device_sn: str):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._device_sn = device_sn
        self._attr_unique_id = f"{device_sn}_inverter_status"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        # Fetch device details stored during __init__.py setup
        device_info_data = self.coordinator.hass.data[DOMAIN][self.coordinator.config_entry.entry_id][DEVICE_INFO_DATA]
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_sn)},
            # Link to the same device as other sensors
            # name, manufacturer, model, sw_version will be inherited from device registry
        )

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            super().available
            and self.coordinator.data is not None
            and self.coordinator.data.get("online", False)
            and self.coordinator.data.get("raw") is not None
            and "runningStatus" in self.coordinator.data["raw"] # Check if status key exists
        )

    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor."""
        raw_data = self.coordinator.data.get("raw", {})
        status_code = raw_data.get("runningStatus")

        # Map status codes to human-readable names (example)
        status_map = {
            "164": "Off-Grid", # From original code comment
            # Add other known status codes from API documentation
            "0": "Waiting",
            "1": "Normal",
            "2": "Fault",
            "3": "Permanent Fault",
            "4": "Updating",
            # ...
        }
        return status_map.get(str(status_code), f"Unknown ({status_code})")

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional state attributes."""
        attrs = {}
        raw_data = self.coordinator.data.get("raw", {})
        device_detail = self.coordinator.data.get("device_detail", {})

        # Add relevant attributes from raw data or device detail
        attrs["raw_status_code"] = raw_data.get("runningStatus")
        attrs["last_cloud_sync"] = device_detail.get("lastCloudSync") # From original code
        # Add other potentially useful attributes like invStatus, dspStatus etc.
        attrs["inv_status"] = raw_data.get("invStatus")
        attrs["dsp_status"] = raw_data.get("dspStatus")
        attrs["sys_status"] = raw_data.get("sysStatus") # From raw data keys

        return attrs
