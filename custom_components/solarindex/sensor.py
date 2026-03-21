"""SolarIndex sensor entities."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SolarIndexCoordinator

_LOGGER = logging.getLogger(__name__)

_DAY_LABELS = [
    "today",
    "tomorrow",
    "day_3",
    "day_4",
    "day_5",
    "day_6",
    "day_7",
    "day_8",
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SolarIndex sensors from a config entry."""
    coordinator: SolarIndexCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[SensorEntity] = []

    # Forecast sensors (today + 7 days)
    for i, label in enumerate(_DAY_LABELS):
        entities.append(SolarIndexForecastSensor(coordinator, entry, i, label))

    # Meta sensors
    entities.append(SolarIndexAccuracySensor(coordinator, entry))
    entities.append(SolarIndexTrainingCountSensor(coordinator, entry))
    entities.append(SolarIndexConditionSensor(coordinator, entry))

    async_add_entities(entities)


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------

class SolarIndexBaseSensor(CoordinatorEntity[SolarIndexCoordinator], SensorEntity):
    """Base class for all SolarIndex sensors."""

    def __init__(
        self,
        coordinator: SolarIndexCoordinator,
        entry: ConfigEntry,
        unique_suffix: str,
        name: str,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_{unique_suffix}"
        self._attr_name = name
        self._attr_has_entity_name = False

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=self._entry.title,
            manufacturer="SolarIndex",
            model="Solar Yield Forecaster",
            entry_type=DeviceEntryType.SERVICE,
        )


# ---------------------------------------------------------------------------
# Forecast sensors
# ---------------------------------------------------------------------------

class SolarIndexForecastSensor(SolarIndexBaseSensor):
    """Forecasted kWh yield for a specific day."""

    def __init__(
        self,
        coordinator: SolarIndexCoordinator,
        entry: ConfigEntry,
        day_index: int,
        label: str,
    ) -> None:
        pretty = label.replace("_", " ").title()
        super().__init__(coordinator, entry, label, f"SolarIndex {pretty}")
        self._day_index = day_index
        self._attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:solar-power"

    @property
    def native_value(self) -> float | None:
        forecasts = (self.coordinator.data or {}).get("forecasts", [])
        if self._day_index < len(forecasts):
            return forecasts[self._day_index].get("expected_kwh")
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        forecasts = (self.coordinator.data or {}).get("forecasts", [])
        if self._day_index >= len(forecasts):
            return {}
        day = forecasts[self._day_index]
        return {
            "date": day.get("date"),
            "weather_code": day.get("weather_code"),
            "radiation_mj_m2": day.get("radiation_sum"),
            "temp_max_c": day.get("temp_max"),
            "temp_min_c": day.get("temp_min"),
            "condition": day.get("condition"),
            "sunshine_hours": round(day.get("sunshine_duration", 0), 1),
            "daylight_hours": round(day.get("daylight_duration", 0), 1),
            "sunrise": day.get("sunrise"),
            "sunset": day.get("sunset"),
        }


# ---------------------------------------------------------------------------
# Meta sensors
# ---------------------------------------------------------------------------

class SolarIndexAccuracySensor(SolarIndexBaseSensor):
    """Model training accuracy in percent."""

    def __init__(self, coordinator: SolarIndexCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "model_accuracy", "SolarIndex Model Accuracy")
        self._attr_native_unit_of_measurement = "%"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:brain"

    @property
    def native_value(self) -> float | None:
        return (self.coordinator.data or {}).get("model_accuracy")


class SolarIndexTrainingCountSensor(SolarIndexBaseSensor):
    """Number of real training entries."""

    def __init__(self, coordinator: SolarIndexCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "training_count", "SolarIndex Training Entries")
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:counter"

    @property
    def native_value(self) -> int | None:
        return (self.coordinator.data or {}).get("training_count")


class SolarIndexConditionSensor(SolarIndexBaseSensor):
    """Today's weather condition bucket (sunny / mixed / overcast)."""

    def __init__(self, coordinator: SolarIndexCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "today_condition", "SolarIndex Today Condition")
        self._attr_icon = "mdi:weather-partly-cloudy"

    @property
    def native_value(self) -> str | None:
        return (self.coordinator.data or {}).get("today_condition")
