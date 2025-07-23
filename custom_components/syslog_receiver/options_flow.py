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
    DEFAULT_CERTFILE,
    DEFAULT_KEYFILE,
    MIN_SEVERITY_LEVELS,
    DEFAULT_ENCODING,
    COMMON_ENCODINGS,
)

class SyslogOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self._config_entry = config_entry
        self._temp_user_input = None

    async def async_step_init(self, user_input=None):
        data = self._config_entry.options or self._config_entry.data

        # Get previously set encoding, fall back to default
        saved_encoding = data.get("encoding", DEFAULT_ENCODING)

        # Build dynamic encoding list: include saved one if it's custom
        encoding_list = list(COMMON_ENCODINGS)
        if saved_encoding and saved_encoding not in COMMON_ENCODINGS:
            encoding_list.insert(-1, saved_encoding)  # Insert before "Other..."

        schema = vol.Schema(
            {
                vol.Required("instance_name", default=data.get("instance_name", DEFAULT_INSTANCE_NAME)): str,
                vol.Required("host", default=data.get("host", DEFAULT_HOST)): str,
                vol.Required("port", default=data.get("port", DEFAULT_PORT)): int,
                vol.Required("protocol", default=data.get("protocol", DEFAULT_PROTOCOL)): vol.In(("UDP", "TCP")),
                vol.Required("use_tls", default=data.get("use_tls", DEFAULT_USE_TLS)): bool,
                vol.Optional("certfile", default=data.get("certfile", DEFAULT_CERTFILE)): cv.string,
                vol.Optional("keyfile", default=data.get("keyfile", DEFAULT_KEYFILE)): cv.string,
                vol.Required("allowed_ips", default=data.get("allowed_ips", DEFAULT_ALLOWED_IPS)): str,
                vol.Required("min_severity", default=data.get("min_severity", DEFAULT_MIN_SEVERITY)): vol.In(tuple(MIN_SEVERITY_LEVELS.keys())),
                vol.Required("enable_sensors", default=data.get("enable_sensors", False)): bool,
                vol.Optional("encoding", default=saved_encoding): vol.In(encoding_list),
            }
        )
        if user_input is not None:
            # Check if user selected "Other…" and trigger custom step
            if user_input.get("encoding") == "Other…":
                self._temp_user_input = user_input
                return await self.async_step_custom_encoding()

            return self.async_create_entry(
                title=user_input.get("instance_name", ""), data=user_input
            )

        return self.async_show_form(step_id="init", data_schema=schema)

    async def async_step_custom_encoding(self, user_input=None):
        custom_encoding_schema = vol.Schema({
            vol.Required("custom_encoding"): str
        })

        if user_input is not None:
            final_input = self._temp_user_input.copy()
            final_input["encoding"] = user_input["custom_encoding"]
            return self.async_create_entry(
                title=final_input.get("instance_name", ""), data=final_input
            )

        return self.async_show_form(
            step_id="custom_encoding",
            data_schema=custom_encoding_schema
        )