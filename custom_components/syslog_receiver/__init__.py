from homeassistant.core import HomeAssistant

DOMAIN = "syslog_receiver"

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the syslog receiver."""
    from .syslog_receiver import SyslogReceiver

    syslog = SyslogReceiver(hass)
    await syslog.start()
    return True

async def async_unload(hass: HomeAssistant):
    """Unload the syslog receiver and clean up resources."""
    syslog = hass.data.get(DOMAIN)
    if syslog:
        await syslog.stop()  # Ensure we stop the server when unloading
    return True