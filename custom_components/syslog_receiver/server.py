import asyncio
import ssl
import logging
import re
import socket
from .const import DOMAIN, MIN_SEVERITY_LEVELS

_LOGGER = logging.getLogger(__name__)

class SyslogServer:
    def __init__(self, hass, config, options):
        self.hass = hass
        self.config = config
        self.options = options
        self.transport = None
        self.server = None
        self.ssl_context = None
        self.sensors = []
        self.last_message = None
        self.last_source = None
        self.last_severity = None

        if config.get("use_tls"):
            self.ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            cert = config.get("certfile")
            key = config.get("keyfile")
            if not cert or not key:
                _LOGGER.error("TLS enabled but certfile/keyfile not set")
                raise ValueError("Missing certfile or keyfile")
            self.ssl_context.load_cert_chain(certfile=cert, keyfile=key)

    async def start(self):
        host = self.config["host"]
        port = self.config["port"]
        protocol = self.config["protocol"]

        if protocol == "UDP":
            loop = asyncio.get_running_loop()
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            except OSError:
                _LOGGER.debug("SO_REUSEPORT not available")
            sock.bind((host, port))
            self.transport, _ = await loop.create_datagram_endpoint(
                lambda: SyslogUDPProtocol(self), sock=sock
            )
            _LOGGER.debug("Started UDP on %s:%s", host, port)
        else:
            try:
                self.server = await asyncio.start_server(
                    self.handle_tcp,
                    host,
                    port,
                    ssl=self.ssl_context
                )
            except ssl.SSLError as ex:
                _LOGGER.error("TLS handshake setup failed: %s", ex)
                raise
            _LOGGER.debug("Started TLS/TCP on %s:%s", host, port)

    async def stop(self):
        if self.transport:
            self.transport.close()
        if self.server:
            self.server.close()
            await self.server.wait_closed()

    def process_message(self, data: bytes, addr):
        message = data.decode(errors="ignore").strip()
        src_ip = addr[0]
        ips = [ip.strip() for ip in self.options.get("allowed_ips", self.config.get("allowed_ips", "")).split(",") if ip.strip()]
        if ips and src_ip not in ips:
            return
        m = re.match(r"<(\d+)>(.*)", message)
        if m:
            pri = int(m.group(1))
            severity = pri & 0x07
            min_level = MIN_SEVERITY_LEVELS.get(self.options.get("min_severity", self.config.get("min_severity", "info")), 6)
            if severity > min_level:
                return
            body = m.group(2).strip()
        else:
            severity = None
            body = message

        self.last_message = body
        self.last_source = src_ip
        self.last_severity = severity
        event_data = {"message": body, "source_ip": src_ip, "severity": severity}
        self.hass.bus.async_fire(f"{DOMAIN}_message", event_data)
        _LOGGER.info("Received %s", event_data)

        for sensor in self.sensors:
            sensor.async_schedule_update_ha_state()

    async def handle_tcp(self, reader, writer):
        """Handle incoming TCP connections."""
        addr = writer.get_extra_info("peername")
        try:
            while True:
                data = await reader.readline()
                if not data:
                    break
                self.process_message(data, addr)
        except Exception:
            _LOGGER.exception("TCP error from %s", addr)
        finally:
            writer.close()
            await writer.wait_closed()

# UDP protocol implementation
class SyslogUDPProtocol(asyncio.DatagramProtocol):
    """UDP protocol wrapper for SyslogServer."""
    def __init__(self, server):
        super().__init__()
        self.server = server

    def connection_made(self, transport):
        # Transport is ready
        pass

    def datagram_received(self, data, addr):
        self.server.process_message(data, addr)