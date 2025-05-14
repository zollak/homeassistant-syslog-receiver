import logging
import socket
import ssl
import asyncio
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval

_LOGGER = logging.getLogger(__name__)

class SyslogReceiver:
    def __init__(self, hass: HomeAssistant):
        """Initialize the SyslogReceiver component."""
        self.hass = hass
        self.host = hass.config_entries.async_entries("syslog_receiver")[0].data.get("host")
        self.port = hass.config_entries.async_entries("syslog_receiver")[0].data.get("port", 514)
        self.username = hass.config_entries.async_entries("syslog_receiver")[0].data.get("username")
        self.password = hass.config_entries.async_entries("syslog_receiver")[0].data.get("password")
        self.tls_enabled = hass.config_entries.async_entries("syslog_receiver")[0].data.get("tls", False)
        self.allowed_ips = hass.config_entries.async_entries("syslog_receiver")[0].data.get("allowed_ips", [])
        self.create_sensor = hass.config_entries.async_entries("syslog_receiver")[0].data.get("create_sensor", False)
        self.server = None
        self.ssl_context = None

        if self.tls_enabled:
            self.ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            # Optionally, load certificates for TLS if needed:
            # self.ssl_context.load_cert_chain(certfile, keyfile)

    async def start(self):
        """Start listening for syslog messages."""
        loop = asyncio.get_event_loop()
        if self.tls_enabled:
            # Use TLS-secured TCP socket
            server = await loop.create_server(
                lambda: SyslogProtocol(self.hass, self.create_sensor),
                self.host,
                self.port,
                ssl=self.ssl_context,
            )
        else:
            # Use regular UDP socket (non-encrypted)
            server = await loop.create_datagram_endpoint(
                lambda: SyslogProtocol(self.hass, self.create_sensor),
                local_addr=(self.host, self.port)
            )
        self.server = server
        _LOGGER.info(f"Syslog receiver started on {self.host}:{self.port}")

    async def stop(self):
        """Stop the syslog server."""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            _LOGGER.info("Syslog receiver stopped.")

class SyslogProtocol(asyncio.DatagramProtocol):
    def __init__(self, hass: HomeAssistant, create_sensor: bool):
        """Initialize the syslog protocol."""
        self.hass = hass
        self.create_sensor = create_sensor
        self.transport = None

    def connection_made(self, transport):
        """Connection is made."""
        self.transport = transport

    def datagram_received(self, data, addr):
        """Receive a syslog message."""
        # Check if the sender's IP is allowed
        if addr[0] not in self.hass.config_entries.async_entries("syslog_receiver")[0].data.get("allowed_ips", []):
            _LOGGER.warning(f"Rejected syslog message from {addr[0]}")
            return  # Ignore message from non-allowed IP

        # Decode the syslog message
        message = data.decode("utf-8")
        severity = self.extract_severity(message)

        # Handle syslog message based on severity (only process critical or higher)
        if severity is not None and severity <= 3:  # Severity 0-3 are critical
            _LOGGER.info(f"Received critical syslog message: {message}")
            if self.create_sensor:
                # Optionally create a sensor to store the message
                self.hass.states.async_set("sensor.syslog_receiver", message)
            self.hass.bus.fire("syslog_received", {"message": message, "severity": severity})
        else:
            _LOGGER.debug(f"Received syslog message: {message}")
            if self.create_sensor:
                # Optionally create a sensor to store the message
                self.hass.states.async_set("sensor.syslog_receiver", message)
            self.hass.bus.fire("syslog_received", {"message": message, "severity": severity})

    def extract_severity(self, message):
        """Extract severity from the syslog message (if in standard format)."""
        if message.startswith("<"):
            pri_end = message.index(">")
            severity = int(message[1:pri_end]) % 8  # Extract severity from PRI
            return severity
        return None
