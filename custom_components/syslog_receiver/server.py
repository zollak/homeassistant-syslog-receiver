import asyncio
import ssl
import logging
import re
import socket
from .const import DOMAIN, MIN_SEVERITY_LEVELS

_LOGGER = logging.getLogger(__name__)

class SyslogServer:
    """Syslog server for receiving, filtering, and dispatching syslog messages over UDP or TCP."""

    def __init__(self, hass, config, options):
        """Initialize the server instance with config and optional overrides."""
        self.hass = hass
        self.config = config
        self.options = options

        self.transports = []  # Active UDP socket transports
        self.servers = []     # Active TCP server instances

        # For sensor entity support
        self.sensors = []
        self.last_message = None
        self.last_source = None
        self.last_severity = None

        # Prepare SSL context if TLS is enabled
        self.ssl_context = None
        if self.__get_option("use_tls"):
            self.ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            cert = self.__get_option("certfile")
            key = self.__get_option("keyfile")
            try:
                self.ssl_context.load_cert_chain(certfile=cert, keyfile=key)
            except ssl.SSLError as ex:
                _LOGGER.error("Failed to load TLS cert/key: %s", ex)
                raise

    def __get_option(self, key: str, default=None):
        """Helper to fetch option override or fallback to config."""
        return self.options.get(key, self.config.get(key, default))
        
    async def start(self):
        """Start the syslog listener(s) for UDP or TCP (optionally with TLS)."""
        host = self.__get_option("host", "")
        port = self.__get_option("port", "")
        proto = self.__get_option("protocol", "").lower()
        loop = asyncio.get_running_loop()

        # Check for malformed IPv6 link-local addresses (scope required)
        if isinstance(host, str) and host.startswith("fe80::") and "%" not in host:
            _LOGGER.error(
                "Link-local IPv6 address '%s' is missing a required interface scope (e.g. %%eth0). "
                "Binding will fail without this. Please update your host value.",
                host
            )
            raise ValueError(f"Invalid IPv6 link-local address '{host}' without scope")

        # Handle UDP sockets
        if proto == "udp":
            _LOGGER.debug(f"getaddrinfo host={host} port={port} config={self.config} options={self.options}")
            infos = socket.getaddrinfo(
                host if len(host) else None, port, # host=None allow both V4 and V6
                family=socket.AF_UNSPEC,
                type=socket.SOCK_DGRAM,
                proto=0,
                flags=socket.AI_PASSIVE
            )
            if not infos:
                _LOGGER.error("getaddrinfo() returned no results for UDP bind: host=%s port=%s", host, port)
                raise ValueError(f"Cannot bind UDP: no usable address found for host={host} port={port}")
            _LOGGER.debug(f"infos={infos}")
            bound = False  # Track if any socket successfully bound

            for af, socktype, proto_num, _, sockaddr in infos:
                _LOGGER.debug(f" af={af} socktype={socktype} proto_num={proto_num}")
                try:
                    sock = socket.socket(af, socktype, proto_num)
                    sock.setblocking(False)
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    try:
                        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
                    except OSError:
                        _LOGGER.debug("SO_REUSEPORT not available on this platform")
                    # Enable dual-stack mode if IPv6 (accepts both v6 and v4 on same port)
                    if af == socket.AF_INET6 and hasattr(socket, "IPV6_V6ONLY"):
                        sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
                    sock.bind(sockaddr)

                    transport, _ = await loop.create_datagram_endpoint(
                        lambda: SyslogUDPProtocol(self),
                        sock=sock
                    )
                    self.transports.append(transport)
                    _LOGGER.debug("Started UDP endpoint on %s [%s]", sockaddr, af)
                    bound = True

                except Exception as ex:
                    _LOGGER.warning("Could not bind UDP %s: %s", sockaddr, ex)
                    try:
                        sock.close()
                    except Exception:
                        pass
                    continue

            if not bound:
                _LOGGER.error("Failed to bind any UDP socket on host=%s port=%s", host, port)
                raise ValueError(f"UDP socket binding failed on {host}:{port}")

        # Handle TCP (plain or TLS)
        elif proto in ("tcp", "tcp+tls"):
            _LOGGER.debug(f"getaddrinfo host={host} port={port} config={self.config} options={self.options}")
            infos = socket.getaddrinfo(
                host, port,
                family=socket.AF_UNSPEC,
                type=socket.SOCK_STREAM,
                proto=0,
                flags=socket.AI_PASSIVE
            )
            if not infos:
                _LOGGER.error("getaddrinfo() returned no results for TCP bind: host=%s port=%s", host, port)
                raise ValueError(f"Cannot bind TCP: no usable address found for host={host} port={port}")
            _LOGGER.debug(f"infos={infos}")
            bound = False

            for af, socktype, proto_num, _, sockaddr in infos:
                _LOGGER.debug(f" af={af} socktype={socktype} proto_num={proto_num}")
                try:
                    sock = socket.socket(af, socktype, proto_num)
                    sock.setblocking(False)
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    try:
                        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
                    except OSError:
                        _LOGGER.debug("SO_REUSEPORT not available on this platform")
                    sock.bind(sockaddr)

                    use_ssl = self.ssl_context if self.__get_option("use_tls") else None
                    server = await asyncio.start_server(
                        self.handle_tcp,
                        sock=sock,
                        ssl=use_ssl
                    )
                    self.servers.append(server)
                    _LOGGER.debug(
                        "Started TCP%s endpoint on %s [%s]",
                        " +TLS" if use_ssl else "",
                        sockaddr,
                        af,
                    )
                    bound = True

                except ssl.SSLError as ex:
                    _LOGGER.error("TLS handshake setup failed on %s: %s", sockaddr, ex)
                    raise
                except Exception as ex:
                    _LOGGER.warning("Could not bind TCP %s: %s", sockaddr, ex)
                    try:
                        sock.close()
                    except Exception:
                        pass
                    continue

            if not bound:
                _LOGGER.error("Failed to bind any TCP socket on host=%s port=%s", host, port)
                raise ValueError(f"TCP socket binding failed on {host}:{port}")

        else:
            raise ValueError(f"Unsupported protocol: {proto}")

    async def stop(self):
        """Stop all listeners and clean up sockets."""
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
        """Handle a received syslog packet: decode, filter, store, and fire an HA event."""
        encoding = self.__get_option("encoding", None)
        try:
            if encoding:
                message = data.decode(encoding, errors="replace").strip()
            else:
                message = data.decode(errors="replace").strip()
        except LookupError:
            _LOGGER.error("Invalid encoding '%s'. Falling back to default.", encoding)
            message = data.decode(errors="replace").strip()
        src_ip = addr[0]

        # Filter by allowed IPs
        raw_ips = self.__get_option("allowed_ips", "")
        ips = [ip.strip() for ip in raw_ips.split(",") if ip.strip()]
        if ips and src_ip not in ips:
            _LOGGER.debug(f"Ignoring message from {src_ip}")
            return

        # Parse syslog priority header (e.g., <14>) and extract severity
        m = re.match(r"<(\d+)>(.*)", message)
        if m:
            pri = int(m.group(1))
            severity = pri & 0x07
            min_level = MIN_SEVERITY_LEVELS.get(self.__get_option("min_severity", "info"), 6)
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

        # Fire event on Home Assistant event bus
        event_data = {"message": body, "source_ip": src_ip, "severity": severity}
        self.hass.bus.async_fire(f"{DOMAIN}_message", event_data)
        _LOGGER.info("Received %s", event_data)

        # Notify all registered sensors to update their state with the latest message
        for sensor in self.sensors:
            sensor.async_schedule_update_ha_state()

    async def handle_tcp(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle a TCP client: receive lines and pass to process_message()."""
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
    """UDP protocol implementation for asyncio loop."""
    def __init__(self, server: SyslogServer):
        super().__init__()
        self.server = server

    def connection_made(self, transport: asyncio.BaseTransport):
        # Transport is connected and ready (no-op for now)
        pass

    def datagram_received(self, data: bytes, addr):
        """Handle each UDP packet received and pass to server logic."""
        self.server.process_message(data, addr)