import logging
import socket
import ssl
import asyncio
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

class SyslogReceiver:
    def __init__(self, hass: HomeAssistant):
        """Initialize the SyslogReceiver component."""
        self.hass = hass
        self.host = None
        self.port = 514
        self.username = None
        self.password = None
        self.tls_enabled = False
        self.allowed_ips = []
        self.create_sensor = False
        self.server = None
        self.ssl_context = None

        # Check if the integration is configured via UI (config_entries) or via configuration.yaml
        if hass.config_entries.async_entries("syslog_receiver"):
            # Get configuration from config_entries (UI-based setup)
            entry = hass.config_entries.async_entries("syslog_receiver")[0]
            self.host = entry.data.get("host")
            self.port = entry.data.get("port", 514)
            self.username = entry.data.get("username")
            self.password = entry.data.get("password")
            self.tls_enabled = entry.data.get("tls", False)
            self.allowed_ips = entry.data.get("allowed_ips", [])
            self.create_sensor = entry.data.get("create_sensor", False)
        else:
            # Get configuration from configuration.yaml (manual setup)
            config = hass.data.get("syslog_receiver", {})
            self.host = config.get("host")
            self.port = config.get("port", 514)
            self.tls_enabled = config.get("tls", False)
            self.allowed_ips = config.get("allowed_ips", [])
            self.create_sensor = config.get("create_sensor", False)

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
            # Force binding to IPv4 (0.0.0.0)
            server = await loop.create_datagram_endpoint(
                lambda: SyslogProtocol(self.hass, self.create_sensor),
                local_addr=("0.0.0.0", self.port)  # Ensure it's bound to IPv4
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
        # Check if the integration is set up via config_entries (UI) or via configuration.yaml
        if self.hass.config_entries.async_entries("syslog_receiver"):
            allowed_ips = self.hass.config_entries.async_entries("syslog_receiver")[0].data.get("allowed_ips", [])
        else:
            allowed_ips = self.hass.data.get("syslog_receiver", {}).get("allowed_ips", [])

        # Check if the sender's IP is allowed
        if addr[0] not in allowed_ips:
            _LOGGER.warning(f"Rejected syslog message from {addr[0]}")
            return  # Ignore message from non-allowed IP

        # Decode the syslog message
        message = data.decode("utf-8")
        severity = self.extract_severity(message)

        if self.create_sensor:
            # Create a sensor for the syslog message, even if the severity is low
            self.hass.states.async_set("sensor.syslog_receiver", message)

        # Handle syslog message based on severity (only process critical or higher)
        if severity is not None and severity <= 3:  # Severity 0-3 are critical
            _LOGGER.info(f"Received critical syslog message: {message}")
            self.hass.bus.fire("syslog_received", {"message": message, "severity": severity})
        else:
            _LOGGER.debug(f"Received syslog message: {message}")
            self.hass.bus.fire("syslog_received", {"message": message, "severity": severity})

    def extract_severity(self, message):
        """Extract severity from the syslog message (if in standard format)."""
        if message.startswith("<"):
            pri_end = message.index(">")
            severity = int(message[1:pri_end]) % 8  # Extract severity from PRI
            return severity
        return None
