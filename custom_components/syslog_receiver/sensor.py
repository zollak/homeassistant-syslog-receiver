from homeassistant.components.sensor import SensorEntity
from .const import DOMAIN

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
        self.server.sensors.append(self)