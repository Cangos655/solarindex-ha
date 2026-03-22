# SolarIndex – Solar Yield Forecasting for Home Assistant

A HACS-compatible custom integration that predicts your daily solar panel energy production using a self-learning ML model trained automatically from your Home Assistant Energy Dashboard data.

## Features

- **Solar yield forecast** (kWh per day, up to 8 days ahead)
- **Automatic ML training** – reads your actual solar production from the HA Energy Dashboard, no manual input needed
- **Weather-bucketed learning** – separate efficiency curves for sunny, mixed, and overcast days
- **Temperature compensation** – accounts for panel efficiency loss at high temperatures
- **11 HA sensor entities** – usable in automations, dashboards, and Energy cards
- **Lovelace card** – available as a separate HACS frontend component ([SolarIndex Card](https://github.com/Cangos655/solarindex-card))
- **Fully configurable via HA UI** – no YAML needed

## Requirements

- Home Assistant 2024.1 or newer
- A solar energy sensor with `device_class: energy` and `state_class: total_increasing` (e.g. from a Fronius, SMA, Huawei, or Shelly inverter integration)
- HACS installed

## Installation

### Via HACS (recommended)

1. Open HACS in Home Assistant
2. Go to **Integrations** → click the three-dot menu → **Custom repositories**
3. Add `https://github.com/Cangos655/solarindex-ha` as type **Integration**
4. Search for **SolarIndex** and install
5. Restart Home Assistant

### Lovelace Card

Install the [SolarIndex Card](https://github.com/Cangos655/solarindex-card) separately via HACS → Frontend.

## Setup

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **SolarIndex**
3. Follow the setup wizard:
   - Choose your location (HA home coordinates or city search)
   - Select your solar energy sensor from the dropdown

The sensor must be a cumulative energy sensor (not a daily-reset measurement). After setup, the model trains automatically within the first update cycle.

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

## How the ML Model Works

The model classifies each day into one of three weather buckets based on the **clear-sky ratio** (sunshine hours / daylight hours):

| Bucket | Ratio | Behaviour |
|--------|-------|-----------|
| ☀️ Sunny | ≥ 0.70 | Direct irradiation dominant |
| ⛅ Mixed | 0.30 – 0.69 | Variable conditions |
| ☁️ Overcast | < 0.30 | Diffuse irradiation |

For each bucket, it learns an **optical efficiency index** from your actual yield data. Newer data is weighted 10× more than older data. The model becomes reliable after ~10–15 real observations (a few weeks of data).

**Temperature compensation** accounts for panel efficiency loss: cells typically run ~10°C warmer than air temperature, losing ~0.4% efficiency per degree above 25°C (STC).

## Data Sources

- **Weather forecast**: [Open-Meteo](https://open-meteo.com/) – free, no API key required
- **Solar production**: Your HA recorder / Energy Dashboard (local data, no cloud)
