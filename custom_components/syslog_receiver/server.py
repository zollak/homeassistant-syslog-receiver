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

        # For UDP transports (may be multiple on v4/v6)
        self.transports = []
        # For TCP servers (may be multiple on v4/v6)
        self.servers = []

        # Sensor support
        self.sensors = []
        self.last_message = None
        self.last_source = None
        self.last_severity = None

        # Prepare SSL context if TLS is enabled
        self.ssl_context = None
        if config.get("use_tls"):
            self.ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            cert = config.get("certfile")
            key = config.get("keyfile")
            try:
                self.ssl_context.load_cert_chain(certfile=cert, keyfile=key)
            except ssl.SSLError as ex:
                _LOGGER.error("Failed to load TLS cert/key: %s", ex)
                raise

    async def start(self):
        """Start the syslog listener(s) for UDP or TCP (with optional TLS)."""
        host = self.config["host"]
        port = self.config["port"]
        proto = self.config["protocol"].lower()
        loop = asyncio.get_running_loop()

        if proto == "udp":
            # Bind for all families (IPv4/IPv6) returned by getaddrinfo
            infos = socket.getaddrinfo(
                host, port,
                family=socket.AF_UNSPEC,
                type=socket.SOCK_DGRAM,
                proto=0,
                flags=socket.AI_PASSIVE
            )
            for af, socktype, proto_num, _, sockaddr in infos:
                try:
                    sock = socket.socket(af, socktype, proto_num)
                    sock.setblocking(False)
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    try:
                        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
                    except OSError:
                        _LOGGER.debug("SO_REUSEPORT not available on this platform")
                    # Allow dual-stack if IPv6
                    if af == socket.AF_INET6 and hasattr(socket, "IPV6_V6ONLY"):
                        sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
                    sock.bind(sockaddr)
                except Exception as ex:
                    _LOGGER.warning("Could not bind UDP %s: %s", sockaddr, ex)
                    try:
                        sock.close()
                    except Exception:
                        pass
                    continue

                transport, _ = await loop.create_datagram_endpoint(
                    lambda: SyslogUDPProtocol(self),
                    sock=sock
                )
                self.transports.append(transport)
                _LOGGER.debug("Started UDP endpoint on %s [%s]", sockaddr, af)

        elif proto in ("tcp", "tcp+tls"):
            # TCP or TCP + TLS
            infos = socket.getaddrinfo(
                host, port,
                family=socket.AF_UNSPEC,
                type=socket.SOCK_STREAM,
                proto=0,
                flags=socket.AI_PASSIVE
            )
            for af, socktype, proto_num, _, sockaddr in infos:
                try:
                    sock = socket.socket(af, socktype, proto_num)
                    sock.setblocking(False)
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    try:
                        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
                    except OSError:
                        _LOGGER.debug("SO_REUSEPORT not available on this platform")
                    sock.bind(sockaddr)
                except Exception as ex:
                    _LOGGER.warning("Could not bind TCP %s: %s", sockaddr, ex)
                    try:
                        sock.close()
                    except Exception:
                        pass
                    continue

                use_ssl = self.ssl_context if self.config.get("use_tls") else None
                try:
                    server = await asyncio.start_server(
                        self.handle_tcp,
                        sock=sock,
                        ssl=use_ssl
                    )
                except ssl.SSLError as ex:
                    _LOGGER.error("TLS handshake setup failed on %s: %s", sockaddr, ex)
                    raise
                self.servers.append(server)
                _LOGGER.debug(
                    "Started TCP%s endpoint on %s [%s]",
                    " +TLS" if use_ssl else "",
                    sockaddr,
                    af,
                )
        else:
            raise ValueError(f"Unsupported protocol {proto}")

    async def stop(self):
        """Stop all syslog listener(s)."""
        # UDP transports
        for transport in self.transports:
            transport.close()
        self.transports.clear()

        # TCP servers
        for server in self.servers:
            server.close()
            await server.wait_closed()
        self.servers.clear()

    def process_message(self, data: bytes, addr):
        """Decode, filter, and fire an event for each incoming syslog message."""
        message = data.decode(errors="ignore").strip()
        src_ip = addr[0]

        # Filter by allowed IPs
        raw_ips = self.options.get("allowed_ips", self.config.get("allowed_ips", ""))
        ips = [ip.strip() for ip in raw_ips.split(",") if ip.strip()]
        if ips and src_ip not in ips:
            return

        # Extract severity from PRI if present
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

        # Store last message for optional sensor
        self.last_message = body
        self.last_source = src_ip
        self.last_severity = severity

        # Fire the Home Assistant event
        event_data = {"message": body, "source_ip": src_ip, "severity": severity}
        self.hass.bus.async_fire(f"{DOMAIN}_message", event_data)
        _LOGGER.info("Received %s", event_data)

        # TODO: check if this two lines are neccessary:
        for sensor in self.sensors:
            sensor.async_schedule_update_ha_state()

    async def handle_tcp(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle an incoming TCP connection and read syslog lines."""
        addr = writer.get_extra_info("peername")
        try:
            while data := await reader.readline():
                self.process_message(data, addr)
        except Exception:
            _LOGGER.exception("TCP error from %s", addr)
        finally:
            writer.close()
            await writer.wait_closed()

class SyslogUDPProtocol(asyncio.DatagramProtocol):
    """UDP protocol wrapper for SyslogServer."""
    def __init__(self, server: SyslogServer):
        super().__init__()
        self.server = server

    def connection_made(self, transport: asyncio.BaseTransport):
        # Transport is ready
        pass

    def datagram_received(self, data: bytes, addr):
        self.server.process_message(data, addr)