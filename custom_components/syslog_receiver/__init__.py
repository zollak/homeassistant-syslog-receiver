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
    old_version = entry.version
    new_version = old_version + 1

    _LOGGER.debug("Migrating configuration entry '%s' from version %s.%s", entry.title, old_version, entry.minor_version)

    data = dict(entry.data)
    modified = False

    # Add 'encoding' if missing
    if "encoding" not in data:
        data["encoding"] = "utf-8"
        _LOGGER.info("Added missing 'encoding' field with default 'utf-8' for config entry '%s'", entry.title)
        modified = True
    else:
        _LOGGER.debug("Encoding already present in config entry '%s', no changes needed", entry.title)

    # If any field was added/modified, update the entry
    if modified:
        hass.config_entries.async_update_entry(entry, data=data, version=new_version)
        _LOGGER.info("Successfully migrated syslog_receiver config entry '%s' from version %s to %s", entry.title, old_version, new_version)
        return True

    _LOGGER.debug("No migration needed for entry '%s'", entry.title)
    return False