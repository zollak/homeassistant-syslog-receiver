import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN
from .server import SyslogServer

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up syslog receiver from a config entry."""
    # Start the syslog server
    server = SyslogServer(hass, entry.data, entry.options)
    await server.start()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = server

    # Forward to sensor platform if sensors enabled
    enable_sensors = entry.options.get(
        "enable_sensors", entry.data.get("enable_sensors", False)
    )
    if enable_sensors:
        await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Stop the syslog server
    server = hass.data[DOMAIN].pop(entry.entry_id)
    await server.stop()

    # Unload sensor platform if it was loaded
    enable_sensors = entry.options.get(
        "enable_sensors", entry.data.get("enable_sensors", False)
    )
    if enable_sensors:
        await hass.config_entries.async_forward_entry_unloads(entry, ["sensor"])

    return True