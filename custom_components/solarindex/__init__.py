"""SolarIndex – Solar yield forecasting integration for Home Assistant."""

from __future__ import annotations

import logging
import pathlib

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import SolarIndexCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]

_CARD_URL = f"/{DOMAIN}/www/solarindex-card.js"


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Register static path for the Lovelace card (runs once at startup)."""
    www_path = pathlib.Path(__file__).parent / "www"
    hass.http.register_static_path(_CARD_URL, str(www_path / "solarindex-card.js"), cache_headers=False)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up SolarIndex from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    coordinator = SolarIndexCoordinator(hass, entry)
    await coordinator._load_history()
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    # Auto-register the Lovelace card resource
    await _async_register_lovelace_resource(hass)

    return True


async def _async_register_lovelace_resource(hass: HomeAssistant) -> None:
    """Add solarindex-card.js as a Lovelace resource if not already present."""
    try:
        lovelace = hass.data.get("lovelace")
        if lovelace is None:
            return
        resources = lovelace.get("resources")
        if resources is None:
            return
        await resources.async_load()
        for resource in resources.async_items():
            if "solarindex-card" in resource.get("url", ""):
                return  # Already registered
        await resources.async_create_item({"res_type": "module", "url": _CARD_URL})
        _LOGGER.info("SolarIndex Lovelace card registered as resource")
    except Exception as exc:  # noqa: BLE001
        _LOGGER.warning("Could not auto-register Lovelace resource: %s", exc)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update (e.g. sensor changed)."""
    await hass.config_entries.async_reload(entry.entry_id)
