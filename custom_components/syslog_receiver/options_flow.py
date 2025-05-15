import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import config_validation as cv
from .const import (
    DEFAULT_HOST,
    DEFAULT_PORT,
    DEFAULT_PROTOCOL,
    DEFAULT_USE_TLS,
    DEFAULT_ALLOWED_IPS,
    DEFAULT_MIN_SEVERITY,
    DEFAULT_INSTANCE_NAME,
    MIN_SEVERITY_LEVELS,
)

class SyslogOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Syslog Receiver."""

    def __init__(self, config_entry):
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        data = self._config_entry.options or self._config_entry.data
        schema = vol.Schema(
            {
                vol.Optional(
                    "instance_name", default=data.get("instance_name", DEFAULT_INSTANCE_NAME)
                ): str,
                vol.Optional("host", default=data.get("host", DEFAULT_HOST)): str,
                vol.Optional("port", default=data.get("port", DEFAULT_PORT)): int,
                vol.Optional(
                    "protocol", default=data.get("protocol", DEFAULT_PROTOCOL)
                ): vol.In(["UDP", "TCP"]),
                vol.Optional(
                    "use_tls", default=data.get("use_tls", DEFAULT_USE_TLS)
                ): bool,
                vol.Optional(
                    "allowed_ips", default=data.get("allowed_ips", DEFAULT_ALLOWED_IPS)
                ): str,  # comma-separated IPs
                vol.Optional(
                    "min_severity", default=data.get("min_severity", DEFAULT_MIN_SEVERITY)
                ): vol.In(tuple(MIN_SEVERITY_LEVELS.keys())),
                vol.Optional(
                    "enable_sensors", default=data.get("enable_sensors", False)
                ): bool,
            }
        )
        if user_input is not None:
            return self.async_create_entry(
                title=user_input.get("instance_name", ""), data=user_input
            )
        return self.async_show_form(step_id="init", data_schema=schema)