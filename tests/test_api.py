import unittest
import httpretty
import json
from pyzabbix import ZabbixAPI


class TestPyZabbix(unittest.TestCase):

    @httpretty.activate
    def test_login(self):
        httpretty.register_uri(
            httpretty.GET,
            "http://example.com/api_jsonrpc.php",
            body=json.dumps({
                "jsonrpc": "2.0",
                "result": "0424bd59b807674191e7d77572075f33",
                "id": 1
            }),
        )

        zapi = ZabbixAPI('http://example.com')
        zapi.login('mylogin', 'mypass')

        # Check request
        self.assertEqual(
            httpretty.last_request().body,
            json.dumps({
                'jsonrpc': '2.0',
                'method': 'user.login',
                'params': {'user': 'mylogin', 'password': 'mypass'},
                'auth': '',
                'id': 0,
            })
        )

        # Check response
        self.assertEqual(zapi.auth, "0424bd59b807674191e7d77572075f33")
