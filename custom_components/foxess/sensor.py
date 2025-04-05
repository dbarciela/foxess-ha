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

from .const import COORDINATOR, DOMAIN, CONF_DEVICE_SN, DEVICE_INFO_DATA, CONF_EXTPV # Added CONF_EXTPV
from .api import FoxEssApiClient # Although not used directly here, good for context
# Assuming EXTENDED_PV_SENSOR_DESCRIPTIONS is defined in definitions.py
from .definitions import SENSOR_DESCRIPTIONS, BATTERY_SETTING_SENSORS, REPORT_SENSORS, EXTENDED_PV_SENSOR_DESCRIPTIONS

_LOGGER = logging.getLogger(__name__)

# (Definitions moved to definitions.py)


def _create_sensors(
    coordinator,
    descriptions: list[SensorEntityDescription],
    sensor_class: type[FoxEssEntity],
    device_sn: str,
    data_source_key: str,
    data_sub_key: str | None = None, # Optional sub-key (e.g., "today" for report)
) -> list[FoxEssEntity]:
    """Helper to create sensor entities from descriptions."""
    entities = []
    source_data = coordinator.data.get(data_source_key, {})
    if data_sub_key:
        source_data = source_data.get(data_sub_key, {}) # Dive into sub-key if provided

    if not isinstance(source_data, dict):
        _LOGGER.warning("Expected dictionary for source '%s' (sub-key: %s), got %s",
                        data_source_key, data_sub_key, type(source_data))
        return [] # Cannot proceed if data structure is wrong

    for description in descriptions:
        if description.key in source_data:
            entities.append(sensor_class(coordinator, description, device_sn))
        else:
            _LOGGER.debug(
                "Skipping sensor %s for %s as key not found in initial data source '%s' (sub-key: %s)",
                description.key, device_sn, data_source_key, data_sub_key
            )
    return entities


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

    # Create entities using the helper function
    entities.extend(_create_sensors(coordinator, SENSOR_DESCRIPTIONS, FoxEssRawSensor, device_sn, "raw"))

    has_battery = bool(device_info_data.get("hasBattery"))
    if has_battery:
        entities.extend(_create_sensors(coordinator, BATTERY_SETTING_SENSORS, FoxEssBatterySettingSensor, device_sn, "battery"))

    # Report data for today is now processed by the coordinator and stored directly under "report"
    entities.extend(_create_sensors(coordinator, REPORT_SENSORS, FoxEssReportSensor, device_sn, "report"))

    # Conditionally add extended PV sensors based on options
    extend_pv = entry.options.get(CONF_EXTPV, False)
    if extend_pv:
        _LOGGER.debug("Adding extended PV sensors (PV5-18) based on options")
        # Note: PV5/6 might overlap with SENSOR_DESCRIPTIONS depending on definition file,
        # _create_sensors should handle duplicates gracefully if keys match.
        # Assuming EXTENDED_PV_SENSOR_DESCRIPTIONS covers PV5-18 or similar range.
        entities.extend(_create_sensors(coordinator, EXTENDED_PV_SENSOR_DESCRIPTIONS, FoxEssRawSensor, device_sn, "raw"))

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
        # Use the config entry's unique ID (either legacy deviceID or new deviceSN)
        # as the base for the sensor's unique ID to ensure continuity.
        config_entry_unique_id = coordinator.config_entry.unique_id
        self._attr_unique_id = f"{config_entry_unique_id}_{description.key}"

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
    def _data_source(self) -> dict | None:
        """Return the specific data source dictionary for this entity type (e.g., raw, battery). Needs override."""
        raise NotImplementedError

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        # Base availability check: coordinator updates, inverter online
        base_available = (
            super().available
            and self.coordinator.data is not None
            and self.coordinator.data.get("online", False)
        )
        if not base_available:
            return False

        # Check if the specific data source exists and the key is present
        data_source = self._data_source
        return (
            data_source is not None
            and self.entity_description.key in data_source
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
    @property
    def _data_source(self) -> dict | None:
        """Return the 'raw' data dictionary."""
        return self.coordinator.data.get("raw")

    def _get_data_value(self, data_key: str) -> Any | None:
        """Get value from the 'raw' data dictionary."""
        source = self._data_source
        return source.get(data_key) if source else None

    # available property now handled by base class + _data_source check


class FoxEssBatterySettingSensor(FoxEssEntity):
    """Sensor reading data from the 'battery' part of the coordinator data."""
    @property
    def _data_source(self) -> dict | None:
        """Return the 'battery' data dictionary."""
        return self.coordinator.data.get("battery")

    def _get_data_value(self, data_key: str) -> Any | None:
        """Get value from the 'battery' data dictionary."""
        source = self._data_source
        return source.get(data_key) if source else None

    # available property now handled by base class + _data_source check


class FoxEssReportSensor(FoxEssEntity):
    """Sensor reading data from the 'report' part of the coordinator data."""
    # This assumes the report data for 'today' is structured appropriately
    # Adjust the key access logic if the API response structure is different

    @property
    def _data_source(self) -> dict | None:
        """Return the 'report' data dictionary (processed for today in coordinator)."""
        # The coordinator's _async_update_data now processes the report list
        # and stores today's values directly in the 'report' key.
        report_data = self.coordinator.data.get("report")
        return report_data if isinstance(report_data, dict) else None

    def _get_data_value(self, data_key: str) -> Any | None:
        """Get value from the processed 'report' data dictionary."""
        # Access the already processed report data for today
        source = self._data_source
        return source.get(data_key) if source else None

    # available property now handled by base class + _data_source check


# --- Example Custom Sensor (Not using EntityDescription) ---
class FoxEssInverterStatusSensor(FoxEssEntity): # Inherit from FoxEssEntity
    """Representation of the Inverter Status."""

    _attr_has_entity_name = True
    _attr_name = "Inverter Status"
    _attr_icon = "mdi:solar-power" # Or mdi:information-outline

    # Note: This sensor doesn't use an EntityDescription like the others
    # We still call the base __init__ but don't need the description param here.
    # We manually set the unique_id and other attributes.
    _attr_entity_description = None # Indicate no description is used

    def __init__(self, coordinator, device_sn: str):
        """Initialize the sensor."""
        # Call super().__init__ without description
        # Need to handle the missing description in the base or bypass parts of it.
        # Let's call CoordinatorEntity.__init__ directly and set necessary attrs.
        CoordinatorEntity.__init__(self, coordinator)
        # SensorEntity doesn't have an __init__ to call directly.

        self._device_sn = device_sn # Needed for device_info from FoxEssEntity
        config_entry_unique_id = coordinator.config_entry.unique_id
        self._attr_unique_id = f"{config_entry_unique_id}_inverter_status"
        # _attr_name and _attr_icon are set as class attributes

    # No need to define entity_description property

    # device_info is now correctly inherited from FoxEssEntity

    # This sensor's availability depends on the 'status' key in 'device_info'
    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        # Check base coordinator status first
        if not CoordinatorEntity.available.fget(self): # Check CoordinatorEntity availability
             return False
        if not self.coordinator.data:
             return False

        # Then check for the specific key required by this sensor in device_info
        device_info_data = self.coordinator.data.get("device_info")
        return device_info_data is not None and "status" in device_info_data

    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor based on device_info status."""
        device_info_data = self.coordinator.data.get("device_info", {})
        status_code = device_info_data.get("status") # Use status from device_info

        # Map status codes based on observed API response and old code logic
        # 1: online, 2: alarm, 3: offline
        status_map = {
            1: "Online",
            2: "Alarm", # Treat alarm as a distinct status
            3: "Offline",
        }
        # Use status_code directly as it's an integer
        return status_map.get(status_code, f"Unknown ({status_code})")

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional state attributes."""
        attrs = {}
        raw_data = self.coordinator.data.get("raw", {})
        device_info_data = self.coordinator.data.get("device_info", {}) # Use correct key

        # Add relevant attributes from raw data or device detail
        attrs["device_status_code"] = device_info_data.get("status") # Add the code used for state
        attrs["raw_running_status"] = raw_data.get("runningStatus") # Keep raw status if needed
        # attrs["last_cloud_sync"] = device_info_data.get("lastCloudSync") # Not available in API response
        # Add other potentially useful attributes like invStatus, dspStatus etc.
        attrs["inv_status"] = raw_data.get("invStatus")
        attrs["dsp_status"] = raw_data.get("dspStatus")
        attrs["sys_status"] = raw_data.get("sysStatus")

        return attrs
