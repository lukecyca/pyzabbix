import json
import logging
import re
import struct
from configparser import ConfigParser
from decimal import Decimal
from pathlib import Path
from socket import AF_UNSPEC, SOCK_STREAM, getaddrinfo, socket
from typing import Callable, List, Optional, Tuple, Union

__all__ = [
    "ZabbixMetric",
    "ZabbixResponse",
    "ZabbixSender",
    "ZabbixSenderError",
]

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class ZabbixResponse:
    _info_regex = re.compile(
        r"[Pp]rocessed:? (\d*);? [Ff]ailed:? (\d*);? "
        r"[Tt]otal:? (\d*);? [Ss]econds spent:? (\d*\.\d*)"
    )

    def __init__(self):
        self._processed = 0
        self._failed = 0
        self._total = 0
        self._time = 0
        self._batch_count = 0

    def parse(self, response: dict) -> None:
        """Parse Zabbix response info."""
        info = response["info"]
        match = self._info_regex.search(info)
        if match is None:
            raise ValueError(f"invalid response.info {info}")

        self._processed += int(match.group(1))
        self._failed += int(match.group(2))
        self._total += int(match.group(3))
        self._time += Decimal(match.group(4))

        self._batch_count += 1

    @property
    def processed(self) -> int:
        return self._processed

    @property
    def failed(self) -> int:
        return self._failed

    @property
    def total(self) -> int:
        return self._total

    @property
    def time(self) -> Decimal:
        return self._time

    @property
    def batch_count(self) -> int:
        return self._batch_count


class ZabbixMetric:
    """`ZabbixMetric` is a metric to send to Zabbix.

    Example:
        ```py
        from pyzabbix import ZabbixMetric

        ZabbixMetric('localhost', 'cpu[usage]', 20)
        ```
    """

    def __init__(
        self,
        host: str,
        key: str,
        value: Union[str, int, float],
        clock: Optional[int] = None,
        ns: Optional[int] = None,  # pylint: disable=invalid-name
    ):
        """
        Create a `ZabbixMetric`.

        Args:
            host: Hostname as it displayed in Zabbix.
            key: Key of the trapper item for this metric.
            value: Metric value.
            clock: Unix timestamp. Current time will be used if not specified.
            ns: Unix timestamp nanoseconds.
        """
        self.host = host
        self.key = key
        self.value = value
        if clock is not None:
            self.clock = clock
            if ns is not None:
                self.ns = ns


class ZabbixSenderError(Exception):
    """
    Error that occurred while sending metrics to a Zabbix server.
    """


class ZabbixSender:
    """`ZabbixSender` sends `ZabbixMetric` to Zabbix.

    Example:
        ```py
        from pyzabbix import ZabbixMetric, ZabbixSender

        metrics = [ZabbixMetric('localhost', 'cpu[usage]', 20)]
        zbx = ZabbixSender('127.0.0.1')
        zbx.send(metrics)
        ```
    """

    _servers: List[Tuple[str, int]]

    def __init__(
        self,
        server: str = "127.0.0.1",
        port: int = 10051,
        *,
        servers: Optional[List[Tuple[str, int]]] = None,
        config: Optional[Union[str, bool]] = None,
        batch_size: int = 250,
        socket_timeout: int = 10,
        socket_wrapper: Optional[Callable[[socket], socket]] = None,
    ):
        """
        Args:
            server: Zabbix server address.
            port: Zabbix server port.
            servers: List of Zabbix servers address and port. If provided,
                    the `server` and `port` arguments will be ignored.
            config: Path to a Zabbix agent configuration file to load settings
                    from. If `True` then `/etc/zabbix/zabbix_agentd.conf` will
                    be used. If provided, the `server`, `port` and `servers`
                    arguments will be ignored.
            batch_size: Number of `ZabbixMetrics` to send in a single request.
            socket_timeout: Timeout in seconds for the socket.
            socket_wrapper: Provide a wrapper function to configure the socket.

                    import ssl
                    from pyzabbix import ZabbixSender

                    socket_options = dict()
                    sender = ZabbixSender(
                        server=zabbix_server,
                        port=zabbix_port,
                        socket_wrapper=lambda sock: ssl.wrap_socket(sock, **socket_options),
                    )

        """

        if config is not None:
            if isinstance(config, bool) and config:
                self._config = Path("/etc/zabbix/zabbix_agentd.conf")
            elif isinstance(config, str):
                self._config = Path(config)
            logger.debug(f"using config: {self._config}")

            self._servers = _get_servers_from_config(self._config)
        else:
            self._servers = servers or [(server, port)]

        self.batch_size = batch_size
        self._socket_timeout = socket_timeout
        self._socket_wrapper = socket_wrapper

    _PROTO_HEADER = b"ZBXD\x01"

    def _create_packet(self, metrics: List[ZabbixMetric]) -> bytes:
        """Create a packet from a list of `ZabbixMetric`."""
        request = {
            "request": "sender data",
            "data": list(map(lambda m: m.__dict__, metrics)),
        }
        payload = json.dumps(request)
        logger.debug(">> %s", payload)
        payload = payload.encode(encoding="utf-8")

        packet = self._PROTO_HEADER
        packet += struct.pack("<Q", len(payload))
        packet += payload

        return packet

    def _get_response(self, sock: socket) -> dict:
        """Get response from Zabbix."""

        # len(_PROTO_HEADER) + len(struct.pack("<Q", len(payload))) = 13
        header = sock.recv(13)
        if len(header) != 13 or not header.startswith(self._PROTO_HEADER):
            raise ZabbixSenderError(f"received invalid response header: {header!r}")

        body_len = struct.unpack("<Q", header[5:])[0]
        body = sock.recv(body_len)

        if len(body) != body_len:
            raise ZabbixSenderError(f"received invalid response body: {body!r}")

        result = json.loads(body.decode("utf-8"))
        logger.debug("<< %s", result)

        return result

    def _socket(self, server: Tuple[str, int]) -> socket:
        """Create a socket based on the server details."""
        host, port = server

        for addr_info in getaddrinfo(host, port, AF_UNSPEC, SOCK_STREAM):
            try:
                return socket(addr_info[0], addr_info[1], addr_info[2])
            except OSError as exception:
                logger.debug(exception)
                sock = None

        if sock is None:
            raise OSError(f"could not create socket for {server}")

    def _send(self, metrics: List[ZabbixMetric]) -> dict:
        """Send the a list of `ZabbixMetric` to Zabbix."""
        packet = self._create_packet(metrics)

        for server in self._servers:
            sock = self._socket(server)

            if self._socket_wrapper:
                sock = self._socket_wrapper(sock)

            sock.settimeout(self._socket_timeout)

            with sock:
                try:
                    sock.connect(server)
                    sock.sendall(packet)
                except TimeoutError as exception:
                    logger.error(f"connection to {server} timed out")
                    raise exception
                except OSError as exception:
                    logger.warning(getattr(exception, "msg", exception))
                    raise exception

                response = self._get_response(sock)

            if response["response"] != "success":
                logger.debug(f"error: {response}")
                raise ZabbixSenderError(f"response failed: {response}")

        return response

    def send(
        self,
        metrics: List[ZabbixMetric],
        *,
        batch_size: Optional[int] = None,
    ) -> ZabbixResponse:
        """
        Send a list of `ZabbixMetric` to Zabbix.

        Args:
            metrics: List of `ZabbixMetric`.
            batch_size: The number of `ZabbixMetrics` to send in a single
                        request. If provided, the value will only be used
                        for this call.
        """
        result = ZabbixResponse()

        batch_size = batch_size or self.batch_size

        for batch_index in range(0, len(metrics), self.batch_size):
            batch = metrics[batch_index : batch_index + self.batch_size]
            result.parse(self._send(batch))

        return result


def get_servers_from_config(filepath: Path) -> List[Tuple[str, int]]:
    """Get Zabbix servers details from a Zabbix config file.

    https://www.zabbix.com/documentation/current/en/manual/appendix/config/zabbix_agentd
    """

    text = filepath.read_text(encoding="utf-8")

    server_match = re.search(r"^Server=(.+)$", text, re.MULTILINE)
    server_active_match = re.search(r"^ServerActive=(.+)$", text, re.MULTILINE)

    # Prefer ServerActive, then try Server and fallback to defaults
    if server_active_match:
        server_kind = "active"
        servers = server_active_match.group(1)
    elif server_match:
        server_kind = "passive"
        servers = server_match.group(1)
    else:
        server_kind = "default"
        servers = "127.0.0.1:10051"

    # Server examples:
    #   Server=127.0.0.1,192.168.1.0/24,::1,2001:db8::/32,zabbix.domain
    #
    # ServerActive examples:
    #   ServerActive=127.0.0.1:10051
    #   ServerActive=127.0.0.1:20051,zabbix.domain,[::1]:30051,::1,[12fc::1]
    #   ServerActive=zabbix.cluster.node1;zabbix.cluster.node2:20051;zabbix.cluster.node3
    #   ServerActive=zabbix.cluster.node1;zabbix.cluster.node2:20051,zabbix.cluster2.node1;zabbix.cluster2.node2,zabbix.domain

    result = []
    for server in servers.split(","):
        server = server.strip()

        if server_kind == "active":
            # IPv6 with port
            if server.startswith("[") and "]:" in server:
                result.append(server.rsplit(":", maxsplit=1))
                continue

            # IPv4 with port
            if ":" in server:
                result.append(server.split(":"))
                continue

        if server_kind == "passive":
            if "/" in server:  # Ignore addresses with CIDR
                continue

            result.append((server, 10051))

    return list(map(lambda s: (s[0], int(s[1])), result))
