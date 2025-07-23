import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN
from .server import SyslogServer

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    server = SyslogServer(hass, entry.data, entry.options)
    try:
        await server.start()
    except Exception as err:
        _LOGGER.error("Failed to start syslog server: %s", err)
        raise
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = server

    enable_sensors = entry.options.get("enable_sensors", entry.data.get("enable_sensors", False))
    if enable_sensors:
        await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    server = hass.data[DOMAIN].pop(entry.entry_id)
    await server.stop()

    enable_sensors = entry.options.get("enable_sensors", entry.data.get("enable_sensors", False))
    if enable_sensors:
        for platform in ["sensor"]:
            await hass.config_entries.async_forward_entry_unload(entry, platform)

    return True

async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate old config entries to the latest version."""
    _LOGGER.debug("Migrating configuration from version %s.%s", entry.version, entry.minor_version)

    if entry.version > 1:
        # This means the user has downgraded from a future version
        _LOGGER.error("You would downgrade newer version of config_entry than version 1. It is not allowed. Please, remove the %s configuration and add create it again.", entry.titlec)
        return False

    # Migrate to version 2 by adding encoding
    if entry.version < 2:
        #_LOGGER.warning("async_migrate_entry CALLED for version %s", entry.version)
        _LOGGER.warning("Migrating config entry %s version %s", entry.title, entry.version)
        data = dict(entry.data)
        if "encoding" not in data:
            data["encoding"] = "utf-8"  # default for backward compatibility
        hass.config_entries.async_update_entry(entry, data=data, version=2)
        _LOGGER.warning("Successfully migrated syslog_receiver config entry %s to version 2", entry.title)
        return True

    return False # No migration needed