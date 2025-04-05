"""API Client for FoxESS Cloud."""
import asyncio
import hashlib
import json
import logging
import time
# import secrets # Removed nonce generation
from datetime import datetime

import aiohttp

# API Endpoints
_ENDPOINT_OA_DOMAIN = "https://www.foxesscloud.com"
_ENDPOINT_OA_BATTERY_SETTINGS = "/op/v0/device/battery/soc/get" # Removed ?sn=
_ENDPOINT_OA_REPORT = "/op/v0/device/report/query"
_ENDPOINT_OA_DEVICE_DETAIL = "/op/v0/device/detail" # Path for URL and signature (matches old code)
_ENDPOINT_OA_DEVICE_VARIABLES = "/op/v0/device/real/query"
_ENDPOINT_OA_DAILY_GENERATION = "/op/v0/device/generation" # Removed ?sn=

# Constants
METHOD_POST = "POST"
METHOD_GET = "GET"
DEFAULT_ENCODING = "UTF-8"
# Using a fixed user agent for now, random one can be added if needed
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36" # Match old code example
DEFAULT_TIMEOUT = 75  # API can be slow

_LOGGER = logging.getLogger(__name__)

# --- Exceptions ---
class FoxEssApiException(Exception):
    """Generic API communication error."""

class FoxEssApiAuthError(FoxEssApiException):
    """API authentication error."""

class FoxEssApiTimeoutError(FoxEssApiException):
    """API timeout error."""

class FoxEssApiResponseError(FoxEssApiException):
    """Invalid API response error."""


class FoxEssApiClient:
    """Handles all communication with the FoxESS Cloud API."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        api_key: str,
        device_sn: str,
    ):
        """Initialize the API client."""
        self._session = session
        self._api_key = api_key
        self._device_sn = device_sn
        self._token = api_key # Use API key directly as token for signature

    @staticmethod
    def _md5c(text="", _type="lower"):
        """Calculate MD5 hash."""
        md5str = hashlib.md5(text.encode(DEFAULT_ENCODING)).hexdigest()
        if _type == "upper":
            return md5str.upper()
        return md5str

    def _get_signature(self, path: str, lang: str = "en") -> str:
        """Generate the API request signature."""
        timestamp = str(round(time.time() * 1000))
        # Nonce is not used in hash calculation or headers in the working version
        # nonce = secrets.token_hex(16) # Removed nonce generation
        # Hash calculation matches working version (path + token + timestamp)
        signature_plain = rf"{path}\r\n{self._token}\r\n{timestamp}" # Use raw f-string like old code/doc example
        signature = self._md5c(signature_plain)

        # Headers match working version EXACTLY (includes token, excludes nonce, excludes Accept, includes Connection: close)
        headers = {
            "User-Agent": USER_AGENT,
            "token": self._token,
            "timestamp": timestamp,
            # "nonce": nonce, # Nonce not sent in old code
            "signature": signature,
            "Content-Type": "application/json",
            # "Accept": "application/json, text/plain, */*", # Accept not sent in old code
            "lang": lang,
            "Connection": "close", # Connection: close was sent in old code
        }
        return headers

    async def _request(self, method: str, path: str, params: dict | None = None, data: dict | None = None) -> dict:
        """Make an API request."""
        url = f"{_ENDPOINT_OA_DOMAIN}{path}" # URL for request uses base path
        # Generate signature using the base path (matches old code)
        headers = self._get_signature(path)
        _LOGGER.debug("Sending %s request to %s with params %s and data %s", method, url, params, data)

        try:
            async with self._session.request(
                method,
                url,
                headers=headers,
                params=params,
                json=data,
                timeout=aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT),
            ) as response:
                response.raise_for_status()  # Raise exception for 4xx/5xx status codes
                resp_text = await response.text()
                _LOGGER.debug("API Response (%s): %s", response.status, resp_text)

                # Handle potential empty responses or non-JSON responses
                if not resp_text:
                    _LOGGER.warning("Received empty response from %s", url)
                    return {} # Or raise FoxEssApiResponseError("Empty response")

                try:
                    resp_json = json.loads(resp_text)
                except json.JSONDecodeError as err:
                    _LOGGER.error("Failed to decode JSON response from %s: %s", url, err)
                    raise FoxEssApiResponseError(f"Invalid JSON response: {resp_text}") from err

                # Check for API-level errors indicated in the response body
                # Adjust based on actual API error structure
                if resp_json.get("errno") != 0:
                    msg = resp_json.get("msg", "Unknown API error")
                    errno = resp_json.get("errno")
                    _LOGGER.error("API returned error for %s: [%s] %s", url, errno, msg)
                    # Example: Check for specific auth error codes
                    if errno in [41800]: # Example error code for invalid token/auth
                         raise FoxEssApiAuthError(f"API Auth Error [{errno}]: {msg}")
                    raise FoxEssApiResponseError(f"API Error [{errno}]: {msg}")

                return resp_json.get("result", {}) # Return the 'result' part or empty dict

        except asyncio.TimeoutError as err:
            _LOGGER.error("Timeout connecting to API: %s", err)
            raise FoxEssApiTimeoutError("API request timed out") from err
        except aiohttp.ClientResponseError as err:
            _LOGGER.error("API request failed (%s): %s", err.status, err.message)
            if err.status in [401, 403]: # Unauthorized or Forbidden
                 raise FoxEssApiAuthError(f"API Auth Error ({err.status}): {err.message}") from err
            raise FoxEssApiException(f"API Request Error ({err.status}): {err.message}") from err
        except aiohttp.ClientError as err:
            _LOGGER.error("API connection error: %s", err)
            raise FoxEssApiException(f"API Connection Error: {err}") from err

    async def get_device_detail(self) -> dict:
        """Fetch device details."""
        # Pass params to _request, which will now use them to construct the full path for signature
        params = {"sn": self._device_sn}
        return await self._request(METHOD_GET, _ENDPOINT_OA_DEVICE_DETAIL, params=params)

    async def get_battery_settings(self) -> dict:
        """Fetch battery settings (SoC limits)."""
        params = {"sn": self._device_sn}
        return await self._request(METHOD_GET, _ENDPOINT_OA_BATTERY_SETTINGS, params=params)

    async def get_report(self) -> dict:
        """Fetch daily, monthly, yearly energy report."""
        today = datetime.now().strftime("%Y-%m-%d")
        payload = {
            "sn": self._device_sn,
            "year": datetime.now().year,
            "month": datetime.now().month,
            "dimension": "day", # Fetch daily data for the current month
            "variableNames": ["generation", "feedin", "gridConsumption", "chargeEnergyToTal", "dischargeEnergyToTal", "loads"]
        }
        # This endpoint seems to return data for the whole month when dimension=day
        # Or whole year when dimension=month. Let's fetch daily for current month.
        return await self._request(METHOD_POST, _ENDPOINT_OA_REPORT, data=payload)


    async def get_report_daily_generation(self) -> dict:
        """Fetch daily generation details."""
        params = {"sn": self._device_sn}
        # This endpoint might require date parameters, check API docs
        # Assuming it defaults to today if not specified
        return await self._request(METHOD_GET, _ENDPOINT_OA_DAILY_GENERATION, params=params)

    async def get_raw_data(self, variables: list | None = None) -> dict:
        """Fetch real-time inverter data."""
        # Default variables if none provided (based on original code's usage)
        if variables is None:
             variables = [
                "ambientTemperation", "batChargePower", "batCurrent", "batDischargePower",
                "batTemperature", "batVolt", "boostTemperation", "chargeTemperature",
                "dcdcStatus", "dspStatus", "ECharge", "EChargeTotal", "EDischarge",
                "EDischargeTotal", "EGeneration", "EGenerationTotal", "EGridCharge",
                "EGridChargeTotal", "EGridDischarge", "EGridDischargeTotal", "EInputTotal",
                "ELoad", "ELoadTotal", "EOutputTotal", "epsCurrentR", "epsCurrentS",
                "epsCurrentT", "epsPower", "epsPowerR", "epsPowerS", "epsPowerT",
                "epsVoltR", "epsVoltS", "epsVoltT", "feedinPower", "generationPower",
                "gridConsumptionPower", "invBatCurrent", "invBatPower", "invBatVolt",
                "invOutputCurrent", "invOutputPower", "invOutputVolt", "invStatus",
                "invTemperation", "loadsPower", "meterPower", "meterPower2", "meterStatus",
                "powerFactor", "pv1Current", "pv1Power", "pv1Volt", "pv2Current",
                "pv2Power", "pv2Volt", "pv3Current", "pv3Power", "pv3Volt", "pv4Current",
                "pv4Power", "pv4Volt", "pvPower", "RCurrent", "reactivePower", "RFreq",
                "RPower", "RVolt", "runningStatus", "SCurrent", "SFreq", "SoC", "SPower",
                "SVolt", "sysStatus", "TCurrent", "TFreq", "TPower", "TVolt",
                "currentFault" # Add fault code variable
            ]
            # Add extended PV strings if needed (based on original CONF_EXTPV)
            # This should ideally be passed based on config
            # for i in range(5, 19):
            #     variables.extend([f"pv{i}Current", f"pv{i}Power", f"pv{i}Volt"])

        payload = {
            "sn": self._device_sn,
            "variables": json.dumps(variables) # API expects a JSON string here
        }
        return await self._request(METHOD_POST, _ENDPOINT_OA_DEVICE_VARIABLES, data=payload)