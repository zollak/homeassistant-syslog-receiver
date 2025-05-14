import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Syslog Receiver sensor based on a config entry."""
    server = hass.data[DOMAIN].get(entry.entry_id)
    if server is None:
        _LOGGER.error("Syslog Receiver server instance not found for entry %s", entry.entry_id)
        return
    sensor = SyslogSensor(server, entry.entry_id)
    async_add_entities([sensor], update_before_add=True)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Syslog Receiver sensor config entry."""
    # No special cleanup needed for SensorEntity unload
    return True

class SyslogSensor(SensorEntity):
    def __init__(self, server, entry_id):
        self.server = server
        self.entry_id = entry_id
        self._attr_name = f"Syslog Receiver {entry_id}"
        self._attr_unique_id = f"syslog_receiver_{entry_id}"

    @property
    def state(self):
        return self.server.last_message

    @property
    def extra_state_attributes(self):
        return {
            "source_ip": self.server.last_source,
            "severity": self.server.last_severity
        }

    async def async_added_to_hass(self):
        """Register sensor update callback on server."""
        self.server.sensors.append(self)