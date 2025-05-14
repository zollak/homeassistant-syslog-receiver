import logging
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_USERNAME, CONF_PASSWORD

_LOGGER = logging.getLogger(__name__)

class SyslogReceiverConfigFlow(config_entries.ConfigFlow, domain="syslog_receiver"):
    """Handle a config flow for Syslog Receiver."""

    def __init__(self):
        """Initialize flow."""
        self._host = None
        self._port = 514
        self._username = None
        self._password = None

    async def async_step_user(self, user_input=None):
        """Handle user input."""
        if user_input is not None:
            self._host = user_input[CONF_HOST]
            self._port = user_input[CONF_PORT]
            self._username = user_input.get(CONF_USERNAME)
            self._password = user_input.get(CONF_PASSWORD)

            return self.async_create_entry(
                title="Syslog Receiver",
                data={
                    CONF_HOST: self._host,
                    CONF_PORT: self._port,
                    CONF_USERNAME: self._username,
                    CONF_PASSWORD: self._password,
                },
            )

        return self.async_show_form(step_id="user")