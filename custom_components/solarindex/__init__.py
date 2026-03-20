"""SolarIndex – Solar yield forecasting integration for Home Assistant."""

from __future__ import annotations

import logging
import pathlib
import shutil

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import SolarIndexCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]

_CARD_FILENAME = "solarindex-card.js"
_CARD_URL = f"/local/{_CARD_FILENAME}"


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Register the Lovelace card JS at startup (called once, before any entries)."""
    await hass.async_add_executor_job(_copy_card_to_www, hass)
    add_extra_js_url(hass, _CARD_URL)
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

    return True


def _copy_card_to_www(hass: HomeAssistant) -> None:
    """Copy solarindex-card.js to /config/www/ (served by HA at /local/)."""
    src = pathlib.Path(__file__).parent / "www" / _CARD_FILENAME
    dst_dir = pathlib.Path(hass.config.config_dir) / "www"
    dst_dir.mkdir(exist_ok=True)
    dst = dst_dir / _CARD_FILENAME
    shutil.copy2(str(src), str(dst))
    _LOGGER.debug("Copied %s to %s", _CARD_FILENAME, dst)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update (e.g. sensor changed)."""
    await hass.config_entries.async_reload(entry.entry_id)
