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

    async def start(self):
        host = self.config["host"]
        port = self.config["port"]
        protocol = self.config["protocol"]

        if protocol == "UDP":
            loop = asyncio.get_running_loop()
            # Create a UDP socket with address reuse
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            except OSError:
                _LOGGER.debug("SO_REUSEPORT not available")
            sock.bind((host, port))
            self.transport, _ = await loop.create_datagram_endpoint(
                lambda: SyslogUDPProtocol(self),
                sock=sock
            )
            _LOGGER.debug("Started UDP syslog server on %s:%s", host, port)
        else:
            self.server = await asyncio.start_server(
                self.handle_tcp, host, port, ssl=self.ssl_context
            )
            _LOGGER.debug("Started TCP syslog server on %s:%s", host, port)

    async def stop(self):
        if self.transport:
            self.transport.close()
        if self.server:
            self.server.close()
            await self.server.wait_closed()

    def process_message(self, data, addr):
        message = data.decode(errors="ignore").strip()
        src_ip = addr[0]

        raw = self.options.get("allowed_ips") if "allowed_ips" in self.options else self.config.get("allowed_ips", "")
        if isinstance(raw, str):
            ips = [ip.strip() for ip in raw.split(",") if ip.strip()]
        elif isinstance(raw, (list, tuple)):
            ips = list(raw)
        else:
            ips = []

        if ips and src_ip not in ips:
            return

        severity = None
        m = re.match(r"<(\d+)>(.*)", message)
        if m:
            pri = int(m.group(1))
            severity = pri & 0x07
            min_sev = self.options.get("min_severity", self.config.get("min_severity", "info"))
            min_level = MIN_SEVERITY_LEVELS.get(min_sev, 6)
            if severity > min_level:
                return
            body = m.group(2).strip()
        else:
            body = message

        self.last_message = body
        self.last_source = src_ip
        self.last_severity = severity

        event_data = {
            "message": body,
            "source_ip": src_ip,
            "severity": severity
        }
        self.hass.bus.async_fire(f"{DOMAIN}_message", event_data)
        _LOGGER.info("Received syslog message: %s", event_data)

        for sensor in self.sensors:
            sensor.async_schedule_update_ha_state()

    async def handle_tcp(self, reader, writer):
        addr = writer.get_extra_info("peername")
        try:
            while True:
                data = await reader.readline()
                if not data:
                    break
                self.process_message(data, addr)
        except Exception:
            _LOGGER.exception("Error handling TCP connection from %s", addr)
        finally:
            writer.close()
            await writer.wait_closed()

class SyslogUDPProtocol(asyncio.DatagramProtocol):
    def __init__(self, server):
        super().__init__()
        self.server = server

    def connection_made(self, transport):
        # Datagram transport is ready
        pass

    def datagram_received(self, data, addr):
        self.server.process_message(data, addr)