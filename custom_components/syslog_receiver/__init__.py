import asyncio
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN
from .server import SyslogServer

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    config = entry.data
    options = entry.options or {}
    server = SyslogServer(hass, config, options)
    await server.start()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = server

    if options.get("enable_sensors"):
        hass.config_entries.async_forward_entry_setup(entry, "sensor")

    entry.async_on_unload(lambda: hass.loop.create_task(server.stop()))
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    server = hass.data[DOMAIN].pop(entry.entry_id)
    await server.stop()

    if entry.options.get("enable_sensors"):
        await hass.config_entries.async_forward_entry_unload(entry, "sensor")
    return True