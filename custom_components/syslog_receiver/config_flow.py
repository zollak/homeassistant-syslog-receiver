import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv
from .const import (
    DOMAIN,
    DEFAULT_HOST,
    DEFAULT_PORT,
    DEFAULT_PROTOCOL,
    DEFAULT_USE_TLS,
    DEFAULT_ALLOWED_IPS,
    DEFAULT_MIN_SEVERITY,
    DEFAULT_INSTANCE_NAME,
    DEFAULT_CERTFILE,
    DEFAULT_KEYFILE,
    MIN_SEVERITY_LEVELS,
    DEFAULT_ENCODING,
    COMMON_ENCODINGS,
)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("instance_name", default=DEFAULT_INSTANCE_NAME): str,
        vol.Required("host", default=DEFAULT_HOST): str,
        vol.Required("port", default=DEFAULT_PORT): int,
        vol.Required("protocol", default=DEFAULT_PROTOCOL): vol.In(("UDP", "TCP")),
        vol.Required("use_tls", default=DEFAULT_USE_TLS): bool,
        vol.Optional("certfile", default=DEFAULT_CERTFILE): cv.string,
        vol.Optional("keyfile", default=DEFAULT_KEYFILE): cv.string,
        vol.Required("allowed_ips", default=DEFAULT_ALLOWED_IPS): str,
        vol.Required("min_severity", default=DEFAULT_MIN_SEVERITY): vol.In(tuple(MIN_SEVERITY_LEVELS.keys())),
        vol.Required("enable_sensors", default=False): bool,
        vol.Optional("encoding", default=DEFAULT_ENCODING): vol.In(COMMON_ENCODINGS),
    }
)

CUSTOM_ENCODING_SCHEMA = vol.Schema({
    vol.Required("custom_encoding"): str,
})

class SyslogConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 2

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            if user_input.get("encoding") == "Other…":
                self._temp_user_input = user_input  # stash for next step
                return await self.async_step_custom_encoding()
            return self.async_create_entry(
                title=user_input["instance_name"],
                data=user_input
            )
        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors
        )

    async def async_step_custom_encoding(self, user_input=None):
        errors = {}
        if user_input is not None:
            encoding = user_input["custom_encoding"]
            data = self._temp_user_input
            data["encoding"] = encoding
            return self.async_create_entry(
                title=data["instance_name"],
                data=data
            )

        return self.async_show_form(
            step_id="custom_encoding",
            data_schema=CUSTOM_ENCODING_SCHEMA,
            errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        from .options_flow import SyslogOptionsFlowHandler
        return SyslogOptionsFlowHandler(config_entry)