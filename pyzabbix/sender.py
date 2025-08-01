# -*- encoding: utf-8 -*-
#
# Copyright © 2014 Alexey Dubkov
#
# This file is part of py-zabbix.
#
# Py-zabbix is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Py-zabbix is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with py-zabbix. If not, see <http://www.gnu.org/licenses/>.

from decimal import Decimal
import inspect
import json
import logging
import socket
import struct
import re

# For python 2 and 3 compatibility
try:
    from StringIO import StringIO
    import ConfigParser as configparser
except ImportError:
    from io import StringIO
    import configparser

from .logger import NullHandler

null_handler = NullHandler()
logger = logging.getLogger(__name__)
logger.addHandler(null_handler)


class ZabbixResponse(object):
    """The :class:`ZabbixResponse` contains the parsed response from Zabbix.
    """
    def __init__(self):
        self._processed = 0
        self._failed = 0
        self._total = 0
        self._time = 0
        self._chunk = 0
        pattern = (r'[Pp]rocessed:? (\d*);? [Ff]ailed:? (\d*);? '
                   r'[Tt]otal:? (\d*);? [Ss]econds spent:? (\d*\.\d*)')
        self._regex = re.compile(pattern)

    def __repr__(self):
        """Represent detailed ZabbixResponse view."""
        result = json.dumps({'processed': self._processed,
                             'failed': self._failed,
                             'total': self._total,
                             'time': str(self._time),
                             'chunk': self._chunk})
        return result

    def parse(self, response):
        """Parse zabbix response."""
        info = response.get('info')
        res = self._regex.search(info)

        self._processed += int(res.group(1))
        self._failed += int(res.group(2))
        self._total += int(res.group(3))
        self._time += Decimal(res.group(4))
        self._chunk += 1

    @property
    def processed(self):
        return self._processed

    @property
    def failed(self):
        return self._failed

    @property
    def total(self):
        return self._total

    @property
    def time(self):
        return self._time

    @property
    def chunk(self):
        return self._chunk


class ZabbixMetric(object):
    """The :class:`ZabbixMetric` contain one metric for zabbix server.

    :type host: str
    :param host: Hostname as it displayed in Zabbix.

    :type key: str
    :param key: Key by which you will identify this metric.

    :type value: str
    :param value: Metric value.

    :type clock: int
    :param clock: Unix timestamp. Current time will used if not specified.

    >>> from pyzabbix import ZabbixMetric
    >>> ZabbixMetric('localhost', 'cpu[usage]', 20)
    """

    def __init__(self, host, key, value, clock=None):
        self.host = str(host)
        self.key = str(key)
        self.value = str(value)
        if clock:
            if isinstance(clock, (float, int)):
                self.clock = int(clock)
            else:
                raise ValueError('Clock must be time in unixtime format')

    def __repr__(self):
        """Represent detailed ZabbixMetric view."""

        result = json.dumps(self.__dict__, ensure_ascii=False)
        logger.debug('%s: %s', self.__class__.__name__, result)

        return result


class ZabbixSender(object):
    """The :class:`ZabbixSender` send metrics to Zabbix server.

    Implementation of
    `zabbix protocol <https://www.zabbix.com/documentation/1.8/protocols>`_.

    :type zabbix_server: str
    :param zabbix_server: Zabbix server ip address. Default: `127.0.0.1`

    :type zabbix_port: int
    :param zabbix_port: Zabbix server port. Default: `10051`

    :type use_config: str
    :param use_config: Path to zabbix_agentd.conf file to load settings from.
         If value is `True` then default config path will used:
         /etc/zabbix/zabbix_agentd.conf

    :type chunk_size: int
    :param chunk_size: Number of metrics send to the server at one time

    :type socket_wrapper: function
    :param socket_wrapper: to provide a socket wrapper function to be used to
         wrap the socket connection to zabbix.
         Example:
            from pyzabbix import ZabbixSender
            import ssl
            secure_connection_option = dict(..)
            zs = ZabbixSender(
                zabbix_server=zabbix_server,
                zabbix_port=zabbix_port,
                socket_wrapper=lambda sock:ssl.wrap_socket(sock,**secure_connection_option)
            )

    :type timeout: int
    :param timeout: Number of seconds before call to Zabbix server times out
         Default: 10
    >>> from pyzabbix import ZabbixMetric, ZabbixSender
    >>> metrics = []
    >>> m = ZabbixMetric('localhost', 'cpu[usage]', 20)
    >>> metrics.append(m)
    >>> zbx = ZabbixSender('127.0.0.1')
    >>> zbx.send(metrics)
    """

    def __init__(self,
                 zabbix_server='127.0.0.1',
                 zabbix_port=10051,
                 use_config=None,
                 chunk_size=250,
                 socket_wrapper=None,
                 timeout=10):

        self.chunk_size = chunk_size
        self.timeout = timeout

        self.socket_wrapper = socket_wrapper
        if use_config:
            self.zabbix_uri = self._load_from_config(use_config)
        else:
            self.zabbix_uri = [(zabbix_server, zabbix_port)]

    def __repr__(self):
        """Represent detailed ZabbixSender view."""

        result = json.dumps(self.__dict__, ensure_ascii=False)
        logger.debug('%s: %s', self.__class__.__name__, result)

        return result

    def _load_from_config(self, config_file):
        """Load zabbix server IP address and port from zabbix agent config
        file.

        If ServerActive variable is not found in the file, it will
        use the default: 127.0.0.1:10051

        :type config_file: str
        :param use_config: Path to zabbix_agentd.conf file to load settings
            from. If value is `True` then default config path will used:
            /etc/zabbix/zabbix_agentd.conf
        """

        if config_file and isinstance(config_file, bool):
            config_file = '/etc/zabbix/zabbix_agentd.conf'

        logger.debug("Used config: %s", config_file)

        #  This is workaround for config wile without sections
        with open(config_file, 'r') as f:
            config_file_data = "[root]\n" + f.read()

        params = {}

        try:
            # python2
            args = inspect.getargspec(
                configparser.RawConfigParser.__init__).args
        except ValueError:
            # python3
            args = inspect.getfullargspec(
                configparser.RawConfigParser.__init__).kwonlyargs

        if 'strict' in args:
            params['strict'] = False

        config_file_fp = StringIO(config_file_data)
        config = configparser.RawConfigParser(**params)
        config.readfp(config_file_fp)
        # Prefer ServerActive, then try Server and fallback to defaults
        if config.has_option('root', 'ServerActive'):
            zabbix_serveractives = config.get('root', 'ServerActive')
        elif config.has_option('root', 'Server'):
            zabbix_serveractives = config.get('root', 'Server')
        else:
            zabbix_serveractives = '127.0.0.1:10051'

        result = []
        for serverport in zabbix_serveractives.split(','):
            if ':' not in serverport:
                serverport = "%s:%s" % (serverport.strip(), 10051)
            server, port = serverport.split(':')
            serverport = (server, int(port))
            result.append(serverport)
        logger.debug("Loaded params: %s", result)

        return result

    def _receive(self, sock, count):
        """Reads socket to receive data from zabbix server.

        :type socket: :class:`socket._socketobject`
        :param socket: Socket to read.

        :type count: int
        :param count: Number of bytes to read from socket.
        """

        buf = b''

        while len(buf) < count:
            chunk = sock.recv(count - len(buf))
            if not chunk:
                break
            buf += chunk

        return buf

    def _create_messages(self, metrics):
        """Create a list of zabbix messages from a list of ZabbixMetrics.

        :type metrics_array: list
        :param metrics_array: List of :class:`zabbix.sender.ZabbixMetric`.

        :rtype: list
        :return: List of zabbix messages.
        """

        messages = []

        # Fill the list of messages
        for m in metrics:
            messages.append(str(m))

        logger.debug('Messages: %s', messages)

        return messages

    def _create_request(self, messages):
        """Create a formatted request to zabbix from a list of messages.

        :type messages: list
        :param messages: List of zabbix messages

        :rtype: list
        :return: Formatted zabbix request
        """

        msg = ','.join(messages)
        request = '{{"request":"sender data","data":[{msg}]}}'.format(msg=msg)
        request = request.encode("utf-8")
        logger.debug('Request: %s', request)

        return request

    def _create_packet(self, request):
        """Create a formatted packet from a request.

        :type request: str
        :param request: Formatted zabbix request

        :rtype: str
        :return: Data packet for zabbix
        """

        data_len = struct.pack('<Q', len(request))
        packet = b'ZBXD\x01' + data_len + request

        def ord23(x):
            if not isinstance(x, int):
                return ord(x)
            else:
                return x

        logger.debug('Packet [str]: %s', packet)
        logger.debug('Packet [hex]: %s',
                     ':'.join(hex(ord23(x))[2:] for x in packet))
        return packet

    def _get_response(self, connection):
        """Get response from zabbix server, reads from self.socket.

        :type connection: :class:`socket._socketobject`
        :param connection: Socket to read.

        :rtype: dict
        :return: Response from zabbix server or False in case of error.
        """

        response_header = self._receive(connection, 13)
        logger.debug('Response header: %s', response_header)

        if (not response_header.startswith(b'ZBXD\x01') or
                len(response_header) != 13):
            logger.debug('Zabbix return not valid response.')
            result = False
        else:
            response_len = struct.unpack('<Q', response_header[5:])[0]
            response_body = connection.recv(response_len)
            result = json.loads(response_body.decode("utf-8"))
            logger.debug('Data received: %s', result)

        try:
            connection.close()
        except socket.error:
            pass

        return result

    def _chunk_send(self, metrics):
        """Send the one chunk metrics to zabbix server.

        :type metrics: list
        :param metrics: List of :class:`zabbix.sender.ZabbixMetric` to send
            to Zabbix

        :rtype: str
        :return: Response from Zabbix Server
        """
        messages = self._create_messages(metrics)
        request = self._create_request(messages)
        packet = self._create_packet(request)

        for host_addr in self.zabbix_uri:
            logger.debug('Sending data to %s', host_addr)

            try:
                # IPv4
                connection_ = socket.socket(socket.AF_INET)
            except socket.error:
                # IPv6
                try:
                    connection_ = socket.socket(socket.AF_INET6)
                except socket.error:
                    raise Exception("Error creating socket for {host_addr}".format(host_addr=host_addr))
            if self.socket_wrapper:
                connection = self.socket_wrapper(connection_)
            else:
                connection = connection_

            connection.settimeout(self.timeout)

            try:
                # server and port must be tuple
                connection.connect(host_addr)
                connection.sendall(packet)
            except socket.timeout:
                logger.error('Sending failed: Connection to %s timed out after'
                             '%d seconds', host_addr, self.timeout)
                connection.close()
                raise socket.timeout
            except socket.error as err:
                # In case of error we should close connection, otherwise
                # we will close it after data will be received.
                logger.warning('Sending failed: %s', getattr(err, 'msg', str(err)))
                connection.close()
                raise err

            response = self._get_response(connection)
            logger.debug('%s response: %s', host_addr, response)

            if response and response.get('response') != 'success':
                logger.debug('Response error: %s}', response)
                raise socket.error(response)

        return response

    def send(self, metrics):
        """Send the metrics to zabbix server.

        :type metrics: list
        :param metrics: List of :class:`zabbix.sender.ZabbixMetric` to send
            to Zabbix

        :rtype: :class:`pyzabbix.sender.ZabbixResponse`
        :return: Parsed response from Zabbix Server
        """
        result = ZabbixResponse()
        for m in range(0, len(metrics), self.chunk_size):
            result.parse(self._chunk_send(metrics[m:m + self.chunk_size]))
        return result
