from homeassistant.helpers.entity import Entity

class SyslogSensor(Entity):
    """Representation of a Syslog Sensor."""

    def __init__(self, message):
        self._message = message
        self._state = message

    @property
    def name(self):
        """Return the name of the sensor."""
        return "Syslog Receiver"

    @property
    def state(self):
        """Return the current state."""
        return self._state

    def update(self, message):
        """Update the state."""
        self._message = message
        self._state = message
