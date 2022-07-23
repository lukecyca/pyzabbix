import json

import httpretty  # type: ignore
import pytest

from pyzabbix import ZabbixAPI, ZabbixAPIException


@httpretty.activate
def test_login():
    httpretty.register_uri(
        httpretty.POST,
        "http://example.com/api_jsonrpc.php",
        body=json.dumps(
            {
                "jsonrpc": "2.0",
                "result": "0424bd59b807674191e7d77572075f33",
                "id": 0,
            }
        ),
    )

    zapi = ZabbixAPI("http://example.com", detect_version=False)
    zapi.login("mylogin", "mypass")

    # Check request
    assert json.loads(httpretty.last_request().body.decode("utf-8")) == {
        "jsonrpc": "2.0",
        "method": "user.login",
        "params": {"user": "mylogin", "password": "mypass"},
        "id": 0,
    }

    assert httpretty.last_request().headers["content-type"] == "application/json-rpc"
    assert httpretty.last_request().headers["user-agent"] == "python/pyzabbix"

    # Check response
    assert zapi.auth == "0424bd59b807674191e7d77572075f33"


@httpretty.activate
def test_host_get():
    httpretty.register_uri(
        httpretty.POST,
        "http://example.com/api_jsonrpc.php",
        body=json.dumps({"jsonrpc": "2.0", "result": [{"hostid": 1234}], "id": 0}),
    )

    zapi = ZabbixAPI("http://example.com", detect_version=False)
    zapi.auth = "123"
    result = zapi.host.get()

    # Check request
    assert json.loads(httpretty.last_request().body.decode("utf-8")) == {
        "jsonrpc": "2.0",
        "method": "host.get",
        "params": {},
        "auth": "123",
        "id": 0,
    }

    # Check response
    assert result == [{"hostid": 1234}]


@pytest.mark.parametrize(
    "server_url, expected",
    [
        ("http://example.com", "http://example.com/api_jsonrpc.php"),
        ("http://example.com/", "http://example.com/api_jsonrpc.php"),
        ("http://example.com/base", "http://example.com/base/api_jsonrpc.php"),
        ("http://example.com/base/", "http://example.com/base/api_jsonrpc.php"),
    ],
)
def test_server_url_update(server_url, expected):
    assert ZabbixAPI(server_url).url == expected


@httpretty.activate
def test_dict_like_access():
    httpretty.register_uri(
        httpretty.POST,
        "http://example.com/api_jsonrpc.php",
        body=json.dumps({"jsonrpc": "2.0", "result": [{"hostid": 1234}], "id": 0}),
    )

    zapi = ZabbixAPI("http://example.com", detect_version=False)
    result = zapi["host"]["get"]()

    assert result == [{"hostid": 1234}]


@httpretty.activate
def test_host_delete():
    httpretty.register_uri(
        httpretty.POST,
        "http://example.com/api_jsonrpc.php",
        body=json.dumps(
            {
                "jsonrpc": "2.0",
                "result": {
                    "itemids": [
                        "22982",
                        "22986",
                    ]
                },
                "id": 0,
            }
        ),
    )

    zapi = ZabbixAPI("http://example.com", detect_version=False)
    zapi.auth = "123"
    result = zapi.host.delete("22982", "22986")

    # Check request

    assert json.loads(httpretty.last_request().body.decode("utf-8")) == {
        "jsonrpc": "2.0",
        "method": "host.delete",
        "params": ["22982", "22986"],
        "auth": "123",
        "id": 0,
    }

    # Check response
    assert set(result["itemids"]) == {"22982", "22986"}


@httpretty.activate
def test_login_with_context():
    httpretty.register_uri(
        httpretty.POST,
        "http://example.com/api_jsonrpc.php",
        body=json.dumps(
            {
                "jsonrpc": "2.0",
                "result": "0424bd59b807674191e7d77572075f33",
                "id": 0,
            }
        ),
    )

    with ZabbixAPI("http://example.com", detect_version=False) as zapi:
        zapi.login("mylogin", "mypass")
        assert zapi.auth == "0424bd59b807674191e7d77572075f33"


@httpretty.activate
def test_detecting_version():
    httpretty.register_uri(
        httpretty.POST,
        "http://example.com/api_jsonrpc.php",
        body=json.dumps(
            {
                "jsonrpc": "2.0",
                "result": "4.0.0",
                "id": 0,
            }
        ),
    )

    zapi_detect = ZabbixAPI("http://example.com")
    assert zapi_detect.api_version() == "4.0.0"


@httpretty.activate
def test_empty_response():
    httpretty.register_uri(
        httpretty.POST,
        "http://example.com/api_jsonrpc.php",
        body="",
    )

    zapi = ZabbixAPI("http://example.com")
    with pytest.raises(ZabbixAPIException, match="Received empty response"):
        zapi.login("mylogin", "mypass")
