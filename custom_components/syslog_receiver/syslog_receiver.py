import logging
import socket
import ssl
import asyncio
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval

_LOGGER = logging.getLogger(__name__)

class SyslogReceiver:
    def __init__(self, hass: HomeAssistant):
        self.hass = hass
        self.host = hass.config_entries.async_entries("syslog_receiver")[0].data.get("host")
        self.port = hass.config_entries.async_entries("syslog_receiver")[0].data.get("port", 514)
        self.username = hass.config_entries.async_entries("syslog_receiver")[0].data.get("username")
        self.password = hass.config_entries.async_entries("syslog_receiver")[0].data.get("password")
        self.server = None

    async def start(self):
        """Start listening for syslog messages."""
        loop = asyncio.get_event_loop()
        self.server = await loop.create_server(
            lambda: SyslogProtocol(self.hass),
            self.host,
            self.port,
        )
        _LOGGER.info(f"Syslog receiver started on {self.host}:{self.port}")

    async def stop(self):
        """Stop the server."""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            _LOGGER.info("Syslog receiver stopped.")

class SyslogProtocol(asyncio.DatagramProtocol):
    def __init__(self, hass: HomeAssistant):
        self.hass = hass
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        """Receive a syslog message."""
        message = data.decode("utf-8")
        _LOGGER.info(f"Received syslog message: {message}")
        # Here you can create a Home Assistant event, for example:
        self.hass.bus.fire("syslog_received", {"message": message})
