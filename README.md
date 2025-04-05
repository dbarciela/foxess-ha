<h2 align="center">
   <a href="https://www.fox-ess.com">FoxESS</a> and<a href="https://www.home-assistant.io"> Home Assistant</a> integration  🏡 ☀
   </br></br>
   <img src="https://github.com/home-assistant/brands/raw/master/custom_integrations/foxess/logo.png" >
   </br>
   <a href="https://github.com/hacs/default"><img src="https://img.shields.io/badge/HACS-default-sucess"></a>
   <a href="https://github.com/macxq/foxess-ha/actions/workflows/HACS.yaml/badge.svg?branch=main"><img src="https://github.com/macxq/foxess-ha/actions/workflows/HACS.yaml/badge.svg?branch=main"/></a>
    <a href="https://github.com/macxq/foxess-ha/actions/workflows/hassfest.yaml/badge.svg"><img src="https://github.com/macxq/foxess-ha/actions/workflows/hassfest.yaml/badge.svg"/></a>
    </br>
</h2>

## ⚙️ Installation & ♻️ Update

Use hacs.io to manage the installation and update process. Right now this integration is part of HACS by default - no more neeed to add it by custom repositories 🥳

## ⌨️ Manual installation 

Create the folder called `foxess` in `/homeassistant/custom_components`

Copy the content of this integrations `custom_components/foxess` folder into your HA `/homeassistant/custom_components/foxess` folder



## 💾 Configuration

Configuration is handled via the Home Assistant UI (Config Flow). YAML configuration under the `sensor:` key is no longer used for setting up new instances, but existing YAML configurations will be imported automatically to preserve history.

**Adding the Integration (New Users):**

1.  Go to **Settings** -> **Devices & Services**.
2.  Click **Add Integration**.
3.  Search for "FoxESS Cloud" and select it.
4.  Enter your **API Key** and **Device SN** (Inverter Serial Number).
    *   **API Key:** Generate this from the 'API Management' section of your profile on the [Foxesscloud.com](https://www.foxesscloud.com/) website.
    *   **Device SN:** Find this under 'Device' -> 'Inverter' on the [Foxesscloud.com](https://www.foxesscloud.com/) website (e.g., `60BHnnnnnnXnnn`).
5.  Click **Submit**. The integration will be set up using your **Device SN** as the unique identifier.

**Existing YAML Users (Migration):**

If you previously configured this integration using `configuration.yaml` under the `sensor:` key:
1.  **Update** the integration via HACS or manually.
2.  **Restart** Home Assistant.
3.  Home Assistant should automatically detect your existing setup and show a notification prompting you to import the configuration. Click **Configure** or **Submit** on the notification.
4.  The import process uses your **legacy `deviceID`** from your YAML file as the unique identifier for the integration entry. **This is crucial for preserving your existing entity history.**
    *   **Finding your legacy `deviceID` (if needed):** If you need to find your old `deviceID` for reference, it was typically found in the URL when viewing the Inverter Details page on the FoxESS Cloud website (often a long alphanumeric string between `%2522` characters, as shown in the image below).
    ![Legacy deviceID location](https://github.com/macxq/foxess-ha/assets/123640536/1e024286-7215-4bab-8e7d-5dfe5e719275)
5.  Any options like `extendPV: true` from your YAML config will also be imported automatically.
6.  After successful import, you can safely **remove** the FoxESS configuration from your `configuration.yaml` file.

**Options (After Setup):**

Once the integration is added (either via UI or import), you can configure additional options:
1.  Go to **Settings** -> **Devices & Services**.
2.  Find the FoxESS Cloud integration card for your inverter and click **Configure**.
3.  **Extend PV:** Check this box if you have an inverter that supports more than 4 PV strings (e.g., Fox R series) to enable sensors for PV strings 5-18. Click **Submit** to save. The integration will automatically reload to apply the change.

**Multi-Inverter Support:**

*   To add multiple inverters, simply repeat the "Add Integration" process via the UI for each inverter, providing its unique **Device SN** and your **API Key**.
*   Home Assistant allows you to rename devices and entities via the UI if desired after setup.
 



## 📊 Provided entities

HA Entity  | Measurement
|---|---|
Inverter |  string  `on-line/off-line/in-alarm` - attributes Master, Manager, Slave versions & Battery details where fitted
Generation Power  |  kW 
Grid Consumption Power  |  kW  
FeedIn Power  |  kW  
Bat Discharge Power  |  kW   
Bat Charge Power  |  kW  
Solar Power | kW
Load Power | kW
Meter2 Power | kW
PV1 Current | A
PV1 Power | kW
PV1 Volt | V
PV2 Current | A
PV2 Power | kW
PV2 Volt | V
PV3 Current | A
PV3 Power | kW
PV3 Volt | V
PV4 Current | A
PV4 Power | kW
PV4 Volt | V
PV Power | kW
R Current | A
R Freq | Hz
R Power | kW
R Volt | V
S Current | A
S Freq | Hz
S Power | kW
S Volt | V
T Current | A
T Freq | Hz
T Power | kW
T Volt | V
Reactive Power | kVar
PV Production Total | kWh
Energy Generated  |  kWh 
Energy Generated Month  |  kWh 
Energy Throughput | kWh
Grid Consumption  |  kWh 
FeedIn  |  kWh  
Solar  |  kWh 
Load |  kWh 
Bat Charge  |  kWh 
Bat Discharge  |  kWh  
Bat SoC | % (single battery systems)
Bat SoC1 | % (dual battery systems)
Bat SoC2 | % (dual battery systems)
Bat SoH | % (single battery systems where BMS supports it)
Inverter Bat Power | kW (negative=charging, positive=discharging)
Inverter Bat Power2 | kW (dual battery systems
Bat Temperature | °C 
Bat Temperature2 | °C (dual battery systems)
Ambient Temp | °C
Boost Temp | °C
Inv Temp | °C
Residual Energy | kWh
minSoC | %
minSoC on Grid | %
Power Factor | %
API Response Time | mS
Running State | string `163: on-grid` (see **Table1**)

**Table1** Possible Running States
Running State
|---------|
160: self-test
161: waiting
162: checking
163: on-grid
164: off-grid
165: fault
166: permanent-fault
167: standby
168: upgrading
169: fct
170: illegal


💡 If you want to understand energy generation per string check out this wiki [article](https://github.com/macxq/foxess-ha/wiki/Understand-PV-string-power-generation-using-foxess-ha)

## 🤔 Troubleshooting 

API Error summary:

- `{"errno":41930,"result":null}` ⟶ incorrect inverter id
- `{"errno":40261,"result":null}` ⟶ incorrect inverter id
- `{"errno":41807,"result":null}` ⟶ wrong user name or password
- `{"errno":41808,"result":null}` ⟶ token expired
- `{"errno":41809,"result":null}` ⟶ invalid token
- `{"errno":40256,"result":null}` ⟶ Request header parameters are missing. Check whether the request headers are consistent with OpenAPI requirements.
- `{"errno":40257,"result":null}` ⟶ Request body parameters are invalid. Check whether the request body is consistent with OpenAPI requirements.
- `{"errno":40400,"result":null}` ⟶ The number of requests is too frequent. Please reduce the frequency of access.


Increase log level in your `/configuration.yaml` by adding:

```yaml
logger:
  default: warning
  logs:
    custom_components.foxess: debug
```

## FoxESS Open API Access and Limits
FoxESS provide an OpenAPI that allows registered users to make request to return datasets.

The OpenAPI access is limited and each user must have a personal_api_key to access it, this personal_api_key can be generated by logging into the FoxESS cloud wesbite - then click on the Profile Icon in the top right hand corner of the screen, select User Profile and then from the menu select API Management, click the button to 'Generate API Key' - this long string of numbers is your personal_api_key and must be used for access to your systems details.

The OpenAPI has a limit of 1,440 API calls per day, after which the OpenAPI will stop responding to requests and generate a "40400" error.

This sounds like a large number of calls, but bear in mind that multiple API calls have to be made on each scan to gain the complete dataset for a system.

The integration paces the number of API calls that are made, with the following frequency -

- Site status and plant details - every 15 minutes
- Real time variables - every 5 minutes
- Cumulative total reports (generation, feedin, gridConsumption, BatterychargeTotal, Batterydischargetotal, home load) - every 15 minutes
- Daily Generation report (Daily Energy Generated - 'total yield') - every 60 minutes
- Battery minSoC settings - every 60 minutes

The integration is using approximately 22 API calls an hour (528 a day and well within the 1,440).

If you have multiple inverters in your account, you will receive 1,440 calls per inverter, so for 2 inverters you will have 2,880 api calls.


## 📚 Usefull wiki articles
* [Understand PV string power generation using foxess ha](https://github.com/macxq/foxess-ha/wiki/Understand-PV-string-power-generation-using-foxess-ha)
* [Sample sensors for better solar monitoring](https://github.com/macxq/foxess-ha/wiki/Sample-sensors-for-better-solar-monitoring)
* [How to fix Energy Dashboard data (statistic data)](https://github.com/macxq/foxess-ha/wiki/How-to-fix-Energy-Dashboard-data-(statistic-data))
