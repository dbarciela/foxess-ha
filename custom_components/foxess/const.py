"""Constants for the FoxESS Cloud integration."""

DOMAIN = "foxess"

# Configuration Keys
CONF_DEVICE_SN = "deviceSN"
CONF_API_KEY = "apiKey"
CONF_DEVICE_ID = "deviceID" # Legacy ID, used for import unique_id
CONF_EXTPV = "extendPV" # Option for extended PV sensors
# Default Values
DEFAULT_NAME = "FoxESS"

# Platforms
PLATFORMS = ["sensor"]

# Coordinator Data Keys (Optional, but good practice)
COORDINATOR = "coordinator"
API_CLIENT = "api_client"
DEVICE_INFO_DATA = "device_info_data" # To store data needed for device_info

# Other constants can be added here as needed
SCAN_INTERVAL_MINUTES = 1 # Default scan interval