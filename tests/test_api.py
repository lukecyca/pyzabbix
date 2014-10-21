import unittest
import httpretty
import json
from pyzabbix import ZabbixAPI


class TestPyZabbix(unittest.TestCase):

    @httpretty.activate
    def test_login(self):
        httpretty.register_uri(
            httpretty.POST,
            "http://example.com/api_jsonrpc.php",
            body=json.dumps({
                "jsonrpc": "2.0",
                "result": "0424bd59b807674191e7d77572075f33",
                "id": 0
            }),
        )

        zapi = ZabbixAPI('http://example.com')
        zapi.login('mylogin', 'mypass')

        # Check request
        self.assertEqual(
            json.loads(httpretty.last_request().body.decode('utf-8')),
            {
                'jsonrpc': '2.0',
                'method': 'user.login',
                'params': {'user': 'mylogin', 'password': 'mypass'},
                'id': 0,
            }
        )
        self.assertEqual(
            httpretty.last_request().headers['content-type'],
            'application/json-rpc'
        )
        self.assertEqual(
            httpretty.last_request().headers['user-agent'],
            'python/pyzabbix'
        )

        # Check response
        self.assertEqual(zapi.auth, "0424bd59b807674191e7d77572075f33")

    @httpretty.activate
    def test_host_get(self):
        httpretty.register_uri(
            httpretty.POST,
            "http://example.com/api_jsonrpc.php",
            body=json.dumps({
                "jsonrpc": "2.0",
                "result": [{"hostid": 1234}],
                "id": 0
            }),
        )

        zapi = ZabbixAPI('http://example.com')
        zapi.auth = "123"
        result = zapi.host.get()

        # Check request
        self.assertEqual(
            json.loads(httpretty.last_request().body.decode('utf-8')),
            {
                'jsonrpc': '2.0',
                'method': 'host.get',
                'params': {},
                'auth': '123',
                'id': 0,
            }
        )

        # Check response
        self.assertEqual(result, [{"hostid": 1234}])

    @httpretty.activate
    def test_host_delete(self):
        httpretty.register_uri(
            httpretty.POST,
            "http://example.com/api_jsonrpc.php",
            body=json.dumps({
                "jsonrpc": "2.0",
                "result": {
                    "itemids": [
                        "22982",
                        "22986"
                    ]
                },
                "id": 0
            }),
        )

        zapi = ZabbixAPI('http://example.com')
        zapi.auth = "123"
        result = zapi.host.delete("22982", "22986")

        # Check request
        self.assertEqual(
            json.loads(httpretty.last_request().body.decode('utf-8')),
            {
                'jsonrpc': '2.0',
                'method': 'host.delete',
                'params': ["22982", "22986"],
                'auth': '123',
                'id': 0,
            }
        )

        # Check response
        self.assertEqual(set(result["itemids"]), set(["22982", "22986"]))
