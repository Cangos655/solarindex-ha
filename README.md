# SolarIndex – Solar Yield Forecasting for Home Assistant

A HACS-compatible custom integration that predicts your daily solar panel energy production using a self-learning ML model trained automatically from your Home Assistant Energy Dashboard data.

## Features

- **8-day solar yield forecast** (kWh per day)
- **Automatic ML training** – reads your actual solar production from HA Energy Dashboard, no manual input needed
- **Weather-bucketed learning** – separate efficiency curves for sunny, mixed, and overcast days
- **Temperature compensation** – accounts for panel efficiency loss at high temperatures
- **11 HA sensor entities** – usable in automations, dashboards, and Energy cards
- **Ready-made Lovelace card** – visual forecast with training progress bar
- **Fully configurable via HA UI** – no YAML needed
- **English + German UI**

## Requirements

- Home Assistant 2024.1 or newer
- A solar energy sensor with `device_class: energy` (e.g. from a Fronius, SMA, Huawei, or Shelly inverter integration)
- HACS installed

## Installation

### Via HACS (recommended)

1. Open HACS in Home Assistant
2. Go to **Integrations** → click the three-dot menu → **Custom repositories**
3. Add `https://github.com/Cangos655/solarindex-dashboard` as type **Integration**
4. Search for **SolarIndex** and install
5. Restart Home Assistant

### Lovelace Card (manual step)

1. Copy `lovelace/solarindex-card.js` to your HA `www/` folder
2. In HA: **Settings → Dashboards → Resources** → Add resource:
   - URL: `/local/solarindex-card.js`
   - Type: JavaScript module

## Setup

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **SolarIndex**
3. Follow the setup wizard:
   - Choose your location (HA home coordinates or city search)
   - Select your solar energy sensor from the dropdown
   - Optionally adjust temperature compensation parameters

## Sensors Created

| Entity | Unit | Description |
|--------|------|-------------|
| `sensor.solarindex_today` | kWh | Forecasted yield today |
| `sensor.solarindex_tomorrow` | kWh | Forecasted yield tomorrow |
| `sensor.solarindex_day_3` … `_day_8` | kWh | Days +2 to +7 |
| `sensor.solarindex_model_accuracy` | % | How well-trained the model is (0–100%) |
| `sensor.solarindex_training_count` | — | Number of real training data points |
| `sensor.solarindex_today_condition` | — | Weather bucket: sunny / mixed / overcast |

Each forecast sensor includes attributes: `date`, `weather_code`, `radiation_mj_m2`, `temp_max_c`, `condition`, `sunrise`, `sunset`.

## Lovelace Card

Add to your dashboard YAML:

```yaml
type: custom:solarindex-card
entity_prefix: sensor.solarindex
title: Solar Forecast
```

## How the ML Model Works

The model classifies each day into one of three weather buckets based on the **clear-sky ratio** (sunshine hours / daylight hours):

| Bucket | Ratio | Behaviour |
|--------|-------|-----------|
| ☀️ Sunny | ≥ 0.70 | Direct irradiation dominant |
| ⛅ Mixed | 0.30 – 0.69 | Variable conditions |
| ☁️ Overcast | < 0.30 | Diffuse irradiation |

For each bucket, it learns an **optical efficiency index** from your actual yield data. Newer data is weighted 10× more than older data. The model becomes reliable after ~10–15 real observations (a few weeks of data).

**Temperature compensation** accounts for panel efficiency loss: cells typically run ~10°C warmer than air temperature, losing ~0.4% efficiency per degree above 25°C (STC).

## Advanced Settings

| Parameter | Default | Description |
|-----------|---------|-------------|
| Temperature coefficient | 0.004 | Efficiency loss per °C above 25°C |
| Cell temp offset | 10 °C | Estimated cell temp above air temp |

These can be changed after setup via **Settings → Devices & Services → SolarIndex → Configure**.

## Data Sources

- **Weather forecast**: [Open-Meteo](https://open-meteo.com/) – free, no API key required
- **Solar production**: Your HA recorder / Energy Dashboard (local data, no cloud)
