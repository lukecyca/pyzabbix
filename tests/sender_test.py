# pylint: disable=protected-access

import json
from pathlib import Path
import struct
from socket import AddressFamily, SocketKind
from unittest import mock
import pytest

from pyzabbix import ZabbixMetric, ZabbixSenderError, ZabbixResponse, ZabbixSender
from pyzabbix.sender import get_servers_from_config


def test_zabbix_response():
    response = ZabbixResponse()
    response.parse(
        {
            "response": "success",
            "info": "processed: 8; failed: 0; total: 8; seconds spent: 0.000703",
        }
    )

    assert response.processed == 8
    assert response.failed == 0
    assert response.total == 8
    assert str(response.time) == "0.000703"
    assert response.batch_count == 1


def test_zabbix_metric():
    metric = ZabbixMetric("host1", "key1", 100500)
    assert metric.__dict__ == {
        "host": "host1",
        "key": "key1",
        "value": 100500,
    }

    metric = ZabbixMetric("host1", "key1", 100500, 1457358608)
    assert metric.__dict__ == {
        "host": "host1",
        "key": "key1",
        "value": 100500,
        "clock": 1457358608,
    }

    metric = ZabbixMetric("host1", "key1", 100500, 1457358608, 704032939)
    assert metric.__dict__ == {
        "host": "host1",
        "key": "key1",
        "value": 100500,
        "clock": 1457358608,
        "ns": 704032939,
    }


def tests_zabbix_sender():
    sender = ZabbixSender()
    assert sender._servers == [("127.0.0.1", 10051)]
    assert sender.batch_size == 250
    assert sender._socket_timeout == 10
    assert sender._socket_wrapper is None


def tests_sender_create_packet():
    metrics = [
        ZabbixMetric("host1", "key1", 1, 1457445366),
        ZabbixMetric("host2", "key2", 2, 1457445366),
    ]
    sender = ZabbixSender()
    result = sender._create_packet(metrics)
    assert result == (
        b'ZBXD\x01\xaa\x00\x00\x00\x00\x00\x00\x00{"request": "sender data", "data": '
        b'[{"host": "host1", "key": "key1", "value": 1, "clock": 1457445366}, {"host":'
        b' "host2", "key": "key2", "value": 2, "clock": 1457445366}]}'
    )


# def tests_sender_create_request_failed():
#     message = [
#         '{"clock": "1457445366", "host: \
#         "host1", "value": "1", "key": "key1"}',
#         '{"clock": "1457445366", "host": \
#         "host2", "value": "2", "key": "key2"}',
#     ]
#     zs = ZabbixSender()
#     result = zs._create_request(message)
#     with pytest.raises(Exception):
#         result = json.loads(result.decode())


# def tests_sender_create_packet():
#     message = [
#         '{"clock": "1457445366", "host": "host1",\
#         "value": "1", "key": "key1"}',
#         '{"clock": "1457445366", "host": "host2",\
#         "value": "2", "key": "key2"}',
#     ]
#     zs = ZabbixSender()
#     request = zs._create_request(message)
#     result = zs._create_packet(request)
#     data_len = struct.pack("<Q", len(request))
#     assert Equal(result[5:13], data_len)
#     assert Equal(result[:13], b"ZBXD\x01\xc4\x00\x00\x00\x00\x00\x00\x00")


# @patch("pyzabbix.sender.socket.socket", autospec=autospec)
# def tests_sender_receive(, mock_socket):
#     mock_data = b"\x01\\\x00\x00\x00\x00\x00\x00\x00"
#     mock_socket.recv.side_effect = (False, b"ZBXD", mock_data)

#     zs = ZabbixSender()
#     result = zs._receive(mock_socket, 13)
#     assert Equal(result, b"ZBXD" + mock_data)
#     assert Equal(mock_socket.recv.call_count, 3)
#     mock_socket.recvassert _has_calls([call(13), call(13), call(9)])

METRICS = [ZabbixMetric("host1", "key1", 100500, 1457358608)]
PROTO_HEAD = b"ZBXD\x01"

SOCK_REQ_PAYLOAD = {
    "request": "sender data",
    "data": [{"host": "host1", "key": "key1", "value": 100500, "clock": 1457358608}],
}
SOCK_REQ_BODY = json.dumps(SOCK_REQ_PAYLOAD).encode("utf-8")
SOCK_REQ_HEADER = PROTO_HEAD + b"l\x00\x00\x00\x00\x00\x00\x00"
assert SOCK_REQ_HEADER == b"ZBXD\x01" + struct.pack("<Q", len(SOCK_REQ_BODY))
assert len(SOCK_REQ_HEADER) == 13

SOCK_RESP_HEADER = PROTO_HEAD + b"Z\x00\x00\x00\x00\x00\x00\x00"
SOCK_RESP_BODY = b'{"response":"success","info":"processed: 1; failed: 0; total: 1; seconds spent: 0.000142"}'
assert SOCK_RESP_HEADER == b"ZBXD\x01" + struct.pack("<Q", len(SOCK_RESP_BODY))
assert len(SOCK_RESP_HEADER) == 13
SOCK_RESP_RESULT = json.loads(SOCK_RESP_BODY.decode("utf-8"))


def tests_sender_get_response():
    print(struct.pack("<Q", len(SOCK_REQ_PAYLOAD)))

    with mock.patch("pyzabbix.sender.socket") as mock_socket:
        mock_socket.recv.side_effect = (SOCK_RESP_HEADER, SOCK_RESP_BODY)

        sender = ZabbixSender()
        result = sender._get_response(mock_socket)
        mock_socket.assert_has_calls([mock.call.recv(13), mock.call.recv(90)])
        assert result == SOCK_RESP_RESULT


@pytest.mark.parametrize(
    "response",
    [
        ((PROTO_HEAD + struct.pack("<Q", len(SOCK_REQ_BODY) - 1), SOCK_RESP_BODY)),
        ((b"IDDQ\x01" + struct.pack("<Q", len(SOCK_REQ_BODY)), SOCK_RESP_BODY)),
    ],
)
def tests_sender_get_response_raises(response):
    with mock.patch("pyzabbix.sender.socket") as mock_socket:
        mock_socket.recv.side_effect = response
        sender = ZabbixSender()
        with pytest.raises(ZabbixSenderError):
            sender._get_response(mock_socket)


def tests_sender_send():
    with mock.patch("pyzabbix.sender.socket") as mock_socket:
        mock_socket.return_value.recv.side_effect = (SOCK_RESP_HEADER, SOCK_RESP_BODY)

        sender = ZabbixSender()
        result = sender.send(METRICS)

        mock_socket.assert_has_calls(
            [
                mock.call(AddressFamily.AF_INET, SocketKind.SOCK_STREAM, 6),
                mock.call().settimeout(10),
                # pylint: disable=unnecessary-dunder-call
                mock.call().__enter__(),
                mock.call().connect(("127.0.0.1", 10051)),
                mock.call().sendall(SOCK_REQ_HEADER + SOCK_REQ_BODY),
                mock.call().recv(13),
                mock.call().recv(90),
                # pylint: disable=unnecessary-dunder-call
                mock.call().__exit__(None, None, None),
            ]
        )

        assert result.total == 1
        assert result.failed == 0
        assert result.processed == 1
        assert result.batch_count == 1


def tests_sender_send_sendall_raises():
    with mock.patch("pyzabbix.sender.socket") as mock_socket:
        mock_socket.return_value.sendall.side_effect = OSError

        sender = ZabbixSender()
        with pytest.raises(OSError):
            sender.send(METRICS)


def tests_sender_send_bad_response():
    with mock.patch("pyzabbix.sender.socket") as mock_socket:
        mock_socket.return_value.recv.side_effect = (
            PROTO_HEAD,
            struct.pack("<Q", len(SOCK_RESP_BODY)),
            SOCK_RESP_BODY,
        )
        sender = ZabbixSender()
        with pytest.raises(ZabbixSenderError):
            sender.send(METRICS)


from textwrap import dedent

# Server examples:
#   Server=127.0.0.1,192.168.1.0/24,::1,2001:db8::/32,zabbix.domain
#
# ServerActive examples:
#   ServerActive=127.0.0.1:10051
#   ServerActive=
#   ServerActive=
#   ServerActive=zabbix.cluster.node1;zabbix.cluster.node2:20051,zabbix.cluster2.node1;zabbix.cluster2.node2,zabbix.domain


@pytest.mark.parametrize(
    "server, server_active, expected",
    [
        (
            "10.10.10.1",
            "",
            [("10.10.10.1", 10051)],
        ),
        (
            "zabbix.ignored.com",
            "10.10.10.1:10053",
            [("10.10.10.1", 10053)],
        ),
        (
            "10.10.10.1,192.168.1.0/24",
            "",
            [("10.10.10.1", 10051)],
        ),
        (
            "127.0.0.1,192.168.1.0/24,::1,2001:db8::/32,zabbix.domain",
            "",
            [("zabbix.example.com", 10051)],
        ),
        (
            "",
            "127.0.0.1:20051,zabbix.domain,[::1]:30051,::1,[12fc::1]",
            [("zabbix.example.com", 10051)],
        ),
        (
            "",
            "zabbix.cluster.node1;zabbix.cluster.node2:20051;zabbix.cluster.node3",
            [("zabbix.example.com", 10051)],
        ),
        (
            "",
            "zabbix.cluster.node1;zabbix.cluster.node2:20051,zabbix.cluster2.node1;zabbix.cluster2.node2,zabbix.domain",
            [("zabbix.example.com", 10051)],
        ),
    ],
)
def test_get_servers_from_config(tmp_path: Path, server, server_active, expected):
    filepath = tmp_path / "zabbix_agentd.conf"
    template = dedent(
        """
        ### Some section
        # Some comment

        Server={server}

        ServerActive={server_active}
        """
    )

    filepath.write_text(template.format(server=server, server_active=server_active))
    assert get_servers_from_config(filepath) == expected


# def test_init_config():
#     folder = os.path.dirname(__file__)
#     filename = os.path.join(folder, "data/zabbix_agentd.conf")
#     zs = ZabbixSender(use_config=filename)
#     assert Equal(zs.__class__.__name__, "ZabbixSender")
#     assert Equal(isinstance(zs.zabbix_uri[0], tuple), True)
#     assert Equal(zs.zabbix_uri[0][0], "192.168.1.2")
#     assert Equal(zs.zabbix_uri[0][1], 10051)


# def test_init_config_exception():
#     folder = os.path.dirname(__file__)
#     filename = os.path.join(folder, "zabbix_agent.conf")
#     with assert Raises(Exception):
#         ZabbixSender(use_config=filename)


# def test_init_config_default():
#     folder = os.path.dirname(__file__)
#     filename = os.path.join(folder, "data/zabbix_agentd.conf")
#     file = open(filename)
#     f = file.read()
#     with patch("pyzabbix.sender.open", mock_open(read_data=f)):
#         zs = ZabbixSender(use_config=True)
#         assert Equal(zs.zabbix_uri, [("192.168.1.2", 10051)])
#     file.close()
