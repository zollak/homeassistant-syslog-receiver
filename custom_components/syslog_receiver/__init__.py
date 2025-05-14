from homeassistant.core import HomeAssistant

DOMAIN = "syslog_receiver"

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the syslog receiver."""
    from .syslog_receiver import SyslogReceiver

    syslog = SyslogReceiver(hass)
    await syslog.start()
    return True