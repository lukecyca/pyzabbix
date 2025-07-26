import pytest
from packaging.version import Version

from pyzabbix import ZabbixAPI, ZabbixAPIException


@pytest.mark.parametrize(
    "server, expected",
    [
        ("http://example.com", "http://example.com/api_jsonrpc.php"),
        ("http://example.com/", "http://example.com/api_jsonrpc.php"),
        ("http://example.com/base", "http://example.com/base/api_jsonrpc.php"),
        ("http://example.com/base/", "http://example.com/base/api_jsonrpc.php"),
    ],
)
def test_server_url_correction(server, expected):
    assert ZabbixAPI(server).url == expected


def _zabbix_requests_mock_factory(requests_mock, *args, **kwargs):
    requests_mock.post(
        "http://example.com/api_jsonrpc.php",
        request_headers={
            "Content-Type": "application/json-rpc",
            "User-Agent": "python/pyzabbix",
            "Cache-Control": "no-cache",
        },
        *args,
        **kwargs,
    )


def test_login(requests_mock):
    _zabbix_requests_mock_factory(
        requests_mock,
        json={
            "jsonrpc": "2.0",
            "result": "0424bd59b807674191e7d77572075f33",
            "id": 0,
        },
    )

    zapi = ZabbixAPI("http://example.com", detect_version=False)
    zapi.login("mylogin", "mypass")

    # Check request
    assert requests_mock.last_request.json() == {
        "jsonrpc": "2.0",
        "method": "user.login",
        "params": {"user": "mylogin", "password": "mypass"},
        "id": 0,
    }

    # Check login
    assert zapi.auth == "0424bd59b807674191e7d77572075f33"


def test_login_with_context(requests_mock):
    _zabbix_requests_mock_factory(
        requests_mock,
        json={
            "jsonrpc": "2.0",
            "result": "0424bd59b807674191e7d77572075f33",
            "id": 0,
        },
    )

    with ZabbixAPI("http://example.com", detect_version=False) as zapi:
        zapi.login("mylogin", "mypass")
        assert zapi.auth == "0424bd59b807674191e7d77572075f33"


@pytest.mark.parametrize(
    "version",
    [
        ("4.0.0"),
        ("5.4.0"),
        ("6.2.0"),
        ("6.2.0beta1"),
        ("6.2.2alpha1"),
    ],
)
def test_login_with_version_detect(requests_mock, version):
    _zabbix_requests_mock_factory(
        requests_mock,
        [
            {
                "json": {
                    "jsonrpc": "2.0",
                    "result": version,
                    "id": 0,
                }
            },
            {
                "json": {
                    "jsonrpc": "2.0",
                    "result": "0424bd59b807674191e7d77572075f33",
                    "id": 0,
                }
            },
        ],
    )

    with ZabbixAPI("http://example.com") as zapi:
        zapi.login("mylogin", "mypass")
        assert zapi.auth == "0424bd59b807674191e7d77572075f33"


def test_attr_syntax_kwargs(requests_mock):
    _zabbix_requests_mock_factory(
        requests_mock,
        json={
            "jsonrpc": "2.0",
            "result": [{"hostid": 1234}],
            "id": 0,
        },
    )

    zapi = ZabbixAPI("http://example.com", detect_version=False)
    zapi.auth = "some_auth_key"
    result = zapi.host.get(hostids=5)

    # Check request
    assert requests_mock.last_request.json() == {
        "jsonrpc": "2.0",
        "method": "host.get",
        "params": {"hostids": 5},
        "auth": "some_auth_key",
        "id": 0,
    }

    # Check response
    assert result == [{"hostid": 1234}]


def test_attr_syntax_args(requests_mock):
    _zabbix_requests_mock_factory(
        requests_mock,
        json={
            "jsonrpc": "2.0",
            "result": {"itemids": ["22982", "22986"]},
            "id": 0,
        },
    )

    zapi = ZabbixAPI("http://example.com", detect_version=False)
    zapi.auth = "some_auth_key"
    result = zapi.host.delete("22982", "22986")

    # Check request
    assert requests_mock.last_request.json() == {
        "jsonrpc": "2.0",
        "method": "host.delete",
        "params": ["22982", "22986"],
        "auth": "some_auth_key",
        "id": 0,
    }

    # Check response
    assert result == {"itemids": ["22982", "22986"]}


def test_attr_syntax_args_and_kwargs_raises():
    with pytest.raises(
        TypeError,
        match="Found both args and kwargs",
    ):
        zapi = ZabbixAPI("http://example.com")
        zapi.host.delete("22982", hostids=5)


@pytest.mark.parametrize(
    "version",
    [
        ("4.0.0"),
        ("4.0.0rc1"),
        ("6.2.0beta1"),
        ("6.2.2alpha1"),
    ],
)
def test_detecting_version(requests_mock, version):
    _zabbix_requests_mock_factory(
        requests_mock,
        json={
            "jsonrpc": "2.0",
            "result": version,
            "id": 0,
        },
    )

    zapi = ZabbixAPI("http://example.com")
    zapi.login("mylogin", "mypass")

    assert zapi.api_version() == version


@pytest.mark.parametrize(
    "data",
    [
        (None),
        ('No groups for host "Linux server".'),
    ],
)
def test_error_response(requests_mock, data):
    _zabbix_requests_mock_factory(
        requests_mock,
        json={
            "jsonrpc": "2.0",
            "error": {
                "code": -32602,
                "message": "Invalid params.",
                **({} if data is None else {"data": data}),
            },
            "id": 0,
        },
    )

    with pytest.raises(
        ZabbixAPIException,
        match=(
            "Error -32602: Invalid params., No data."
            if data is None
            else f"Error -32602: Invalid params., {data}"
        ),
    ):
        zapi = ZabbixAPI("http://example.com")
        zapi.host.get()


def test_empty_response(requests_mock):
    _zabbix_requests_mock_factory(
        requests_mock,
        body="",
    )

    with pytest.raises(ZabbixAPIException, match="Received empty response"):
        zapi = ZabbixAPI("http://example.com")
        zapi.login("mylogin", "mypass")


@pytest.mark.parametrize(
    "version",
    [
        ("4.0.0"),
        ("5.4.0"),
        ("6.2.0"),
    ],
)
def test_do_request(requests_mock, version):
    _zabbix_requests_mock_factory(
        requests_mock,
        json={
            "jsonrpc": "2.0",
            "result": [{"hostid": 1234}],
            "id": 0,
        },
    )

    zapi = ZabbixAPI("http://example.com", detect_version=False)
    zapi.version = Version(version)
    zapi.auth = "some_auth_key"
    result = zapi["host"]["get"]()

    # Check response
    assert result == [{"hostid": 1234}]

    # Check request
    found = requests_mock.last_request
    expect_json = {
        "jsonrpc": "2.0",
        "method": "host.get",
        "params": {},
        "id": 0,
    }
    expect_headers = {
        "Cache-Control": "no-cache",
        "Content-Type": "application/json-rpc",
        "User-Agent": "python/pyzabbix",
    }

    if zapi.version < Version("6.4.0"):
        expect_json["auth"] = "some_auth_key"
    else:
        expect_headers["Authorization"] = "Bearer some_auth_key"

    assert found.json() == expect_json
    assert found.headers.items() >= expect_headers.items()
