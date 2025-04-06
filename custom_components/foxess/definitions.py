"""Sensor entity descriptions for the FoxESS Cloud integration."""

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntityDescription,
    SensorStateClass,
)
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

# --- Sensor Entity Descriptions ---
# Descriptions for sensors pulling data from the 'raw' API endpoint
SENSOR_DESCRIPTIONS: tuple[SensorEntityDescription, ...] = (
    # PV Power Sensors
    SensorEntityDescription(key="pv1Power", name="PV1 Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),
    SensorEntityDescription(key="pv2Power", name="PV2 Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),
    SensorEntityDescription(key="pv3Power", name="PV3 Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),
    SensorEntityDescription(key="pv4Power", name="PV4 Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),
    # Add PV5, PV6 etc. if needed, potentially dynamically
    SensorEntityDescription(key="pvPower", name="PV Power Total", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),

    # PV Voltage Sensors
    SensorEntityDescription(key="pv1Volt", name="PV1 Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT),
    SensorEntityDescription(key="pv2Volt", name="PV2 Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT),
    SensorEntityDescription(key="pv3Volt", name="PV3 Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT),
    SensorEntityDescription(key="pv4Volt", name="PV4 Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT),

    # PV Current Sensors
    SensorEntityDescription(key="pv1Current", name="PV1 Current", native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT),
    SensorEntityDescription(key="pv2Current", name="PV2 Current", native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT),
    SensorEntityDescription(key="pv3Current", name="PV3 Current", native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT),
    SensorEntityDescription(key="pv4Current", name="PV4 Current", native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT),

    # Grid Sensors (R, S, T phases)
    SensorEntityDescription(key="RVolt", name="Grid Voltage R", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT),
    SensorEntityDescription(key="SVolt", name="Grid Voltage S", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT),
    SensorEntityDescription(key="TVolt", name="Grid Voltage T", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT),
    SensorEntityDescription(key="RCurrent", name="Grid Current R", native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT),
    SensorEntityDescription(key="SCurrent", name="Grid Current S", native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT),
    SensorEntityDescription(key="TCurrent", name="Grid Current T", native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT),
    SensorEntityDescription(key="RPower", name="Grid Power R", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),
    SensorEntityDescription(key="SPower", name="Grid Power S", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),
    SensorEntityDescription(key="TPower", name="Grid Power T", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),
    SensorEntityDescription(key="RFreq", name="Grid Frequency R", native_unit_of_measurement=UnitOfFrequency.HERTZ, device_class=SensorDeviceClass.FREQUENCY, state_class=SensorStateClass.MEASUREMENT),
    SensorEntityDescription(key="SFreq", name="Grid Frequency S", native_unit_of_measurement=UnitOfFrequency.HERTZ, device_class=SensorDeviceClass.FREQUENCY, state_class=SensorStateClass.MEASUREMENT),
    SensorEntityDescription(key="TFreq", name="Grid Frequency T", native_unit_of_measurement=UnitOfFrequency.HERTZ, device_class=SensorDeviceClass.FREQUENCY, state_class=SensorStateClass.MEASUREMENT),

    # General Power Sensors
    SensorEntityDescription(key="generationPower", name="Generation Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),
    SensorEntityDescription(key="gridConsumptionPower", name="Grid Consumption Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),
    SensorEntityDescription(key="feedinPower", name="FeedIn Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),
    SensorEntityDescription(key="batDischargePower", name="Battery Discharge Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),
    SensorEntityDescription(key="batChargePower", name="Battery Charge Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),
    SensorEntityDescription(key="loadsPower", name="Load Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),
    SensorEntityDescription(key="meterPower2", name="Meter Power 2", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT), # Check unit/class
    SensorEntityDescription(key="reactivePower", name="Reactive Power", native_unit_of_measurement=UnitOfReactivePower.VOLT_AMPERE_REACTIVE, device_class=SensorDeviceClass.REACTIVE_POWER, state_class=SensorStateClass.MEASUREMENT),

    # Battery Sensors
    SensorEntityDescription(key="SoC", name="Battery SoC", native_unit_of_measurement=PERCENTAGE, device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT),
    SensorEntityDescription(key="SoC_1", name="Battery SoC 1", native_unit_of_measurement=PERCENTAGE, device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT), # If multiple batteries
    SensorEntityDescription(key="SoC_2", name="Battery SoC 2", native_unit_of_measurement=PERCENTAGE, device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT), # If multiple batteries
    SensorEntityDescription(key="SOH", name="Battery SoH", native_unit_of_measurement=PERCENTAGE, state_class=SensorStateClass.MEASUREMENT), # No specific device class for SoH
    SensorEntityDescription(key="batTemperature", name="Battery Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),
    SensorEntityDescription(key="batTemperature_2", name="Battery Temperature 2", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),
    SensorEntityDescription(key="invBatPower", name="Inverter Battery Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),
    SensorEntityDescription(key="invBatPower_2", name="Inverter Battery Power 2", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),

    # Temperature Sensors
    SensorEntityDescription(key="ambientTemperation", name="Ambient Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),
    SensorEntityDescription(key="boostTemperation", name="Boost Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),
    SensorEntityDescription(key="invTemperation", name="Inverter Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),

    # Other Sensors
    SensorEntityDescription(key="powerFactor", name="Power Factor", native_unit_of_measurement=None, device_class=SensorDeviceClass.POWER_FACTOR, state_class=SensorStateClass.MEASUREMENT),
    SensorEntityDescription(key="currentFault", name="Current Fault Code", icon="mdi:alert-circle-outline"), # No unit/device_class needed
    # Add descriptions for ETotal etc. if needed
)

# Sensors that need data from the 'battery' part of coordinator data
BATTERY_SETTING_SENSORS: tuple[SensorEntityDescription, ...] = (
     SensorEntityDescription(key="minGridSoc", name="Min SoC (On Grid)", native_unit_of_measurement=PERCENTAGE, device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT),
     SensorEntityDescription(key="minSoc", name="Min SoC (Off Grid)", native_unit_of_measurement=PERCENTAGE, device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT),
)

# Sensors that need data from the 'report' part of coordinator data
# Keys here must match the structure returned by get_report in api.py
REPORT_SENSORS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(key="generation", name="Energy Generated Today", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING),
    SensorEntityDescription(key="feedin", name="Energy FeedIn Today", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING),
    SensorEntityDescription(key="gridConsumption", name="Energy Grid Consumption Today", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING),
    SensorEntityDescription(key="chargeEnergyToTal", name="Energy Battery Charge Today", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING),
    SensorEntityDescription(key="dischargeEnergyToTal", name="Energy Battery Discharge Today", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING),
    SensorEntityDescription(key="loads", name="Energy Load Today", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING),
    # Add Month / Cumulative if API provides them consistently
)