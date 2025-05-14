import logging
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_USERNAME, CONF_PASSWORD, CONF_TLS, CONF_ALLOWED_IPS, CONF_CREATE_SENSOR

_LOGGER = logging.getLogger(__name__)

class SyslogReceiverConfigFlow(config_entries.ConfigFlow, domain="syslog_receiver"):
    """Handle a config flow for Syslog Receiver."""

    def __init__(self):
        """Initialize flow."""
        self._host = None
        self._port = 514
        self._username = None
        self._password = None
        self._tls = False
        self._allowed_ips = []
        self._create_sensor = False

    async def async_step_user(self, user_input=None):
        """Handle user input."""
        if user_input is not None:
            self._host = user_input[CONF_HOST]
            self._port = user_input[CONF_PORT]
            self._username = user_input.get(CONF_USERNAME)
            self._password = user_input.get(CONF_PASSWORD)
            self._tls = user_input.get(CONF_TLS, False)
            self._allowed_ips = user_input.get(CONF_ALLOWED_IPS, [])
            self._create_sensor = user_input.get(CONF_CREATE_SENSOR, False)

            return self.async_create_entry(
                title="Syslog Receiver",
                data={
                    CONF_HOST: self._host,
                    CONF_PORT: self._port,
                    CONF_USERNAME: self._username,
                    CONF_PASSWORD: self._password,
                    CONF_TLS: self._tls,
                    CONF_ALLOWED_IPS: self._allowed_ips,
                    CONF_CREATE_SENSOR: self._create_sensor,
                },
            )

        return self.async_show_form(
            step_id="user",
            data_schema=self._get_user_input_schema(),
        )

    def _get_user_input_schema(self):
        """Create the input schema with an option for the sensor."""
        from homeassistant.core import HomeAssistant
        return {
            vol.Required(CONF_HOST, default="0.0.0.0"): str,
            vol.Optional(CONF_PORT, default=514): int,
            vol.Optional(CONF_TLS, default=False): bool,
            vol.Optional(CONF_CREATE_SENSOR, default=False): bool,
            vol.Optional(CONF_ALLOWED_IPS, default=[]): list,
        }
