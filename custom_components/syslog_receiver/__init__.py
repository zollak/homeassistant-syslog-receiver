import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN
from .server import SyslogServer

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    server = SyslogServer(hass, entry.data, entry.options)
    await server.start()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = server

    enable_sensors = entry.options.get("enable_sensors", entry.data.get("enable_sensors", False))
    if enable_sensors:
        # Use plural API to avoid deprecation
        await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    server = hass.data[DOMAIN].pop(entry.entry_id)
    await server.stop()

    enable_sensors = entry.options.get("enable_sensors", entry.data.get("enable_sensors", False))
    if enable_sensors:
        # Use plural API to avoid deprecation
        await hass.config_entries.async_forward_entry_unloads(entry, ["sensor"])

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    server = hass.data[DOMAIN].pop(entry.entry_id)
    await server.stop()

    enable_sensors = entry.options.get("enable_sensors", entry.data.get("enable_sensors", False))
    if enable_sensors:
        await hass.config_entries.async_forward_entry_unload(entry, "sensor")

    return True