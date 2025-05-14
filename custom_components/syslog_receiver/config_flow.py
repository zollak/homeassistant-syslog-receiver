import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from .const import (
    DOMAIN, DEFAULT_HOST, DEFAULT_PORT, DEFAULT_PROTOCOL,
    DEFAULT_USE_TLS, DEFAULT_MIN_SEVERITY, MIN_SEVERITY_LEVELS
)

STEP_USER_DATA_SCHEMA = vol.Schema({
    vol.Required("host", default=DEFAULT_HOST): str,
    vol.Required("port", default=DEFAULT_PORT): int,
    vol.Required("protocol", default=DEFAULT_PROTOCOL): vol.In(["UDP", "TCP"]),
    vol.Required("use_tls", default=DEFAULT_USE_TLS): bool,
    vol.Required("allowed_ips", default=""): str,
    vol.Required("min_severity", default=DEFAULT_MIN_SEVERITY): vol.In(list(MIN_SEVERITY_LEVELS.keys())),
    vol.Required("enable_sensors", default=False): bool,
})

class SyslogConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Syslog Receiver."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            return self.async_create_entry(title="Syslog Receiver", data=user_input)
        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Allow reconfiguration via the UI."""
        from .options_flow import SyslogOptionsFlowHandler
        return SyslogOptionsFlowHandler(config_entry)