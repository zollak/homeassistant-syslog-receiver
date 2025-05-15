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
    async_add_entities: AddEntitiesCallback,
) -> None:
    server = hass.data[DOMAIN].get(entry.entry_id)
    if not server:
        _LOGGER.error("No server instance for entry %s", entry.entry_id)
        return

    name = entry.data.get("instance_name", entry.title)
    async_add_entities([SyslogSensor(server, entry.entry_id, name)], update_before_add=True)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    return True

class SyslogSensor(SensorEntity):
    def __init__(self, server, entry_id: str, name: str):
        self.server = server
        self.entry_id = entry_id
        self._attr_name = name
        self._attr_unique_id = f"{DOMAIN}_{entry_id}"

    @property
    def state(self):
        return self.server.last_message

    @property
    def extra_state_attributes(self):
        return {"source_ip": self.server.last_source, "severity": self.server.last_severity}

    async def async_added_to_hass(self):
        self.server.sensors.append(self)