import asyncio
import ssl
import logging
import re

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
            self.transport, _ = await loop.create_datagram_endpoint(
                lambda: SyslogUDPProtocol(self),
                local_addr=(host, port)
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

        if self.options.get("allowed_ips") and src_ip not in self.options["allowed_ips"]:
            return

        severity = None
        m = re.match(r"<(\d+)>(.*)", message)
        if m:
            pri = int(m.group(1))
            severity = pri & 0x07
            min_level = MIN_SEVERITY_LEVELS.get(self.options.get("min_severity", "info"), 6)
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

class SyslogUDPProtocol:
    def __init__(self, server):
        self.server = server

    def datagram_received(self, data, addr):
        self.server.process_message(data, addr)