from os import getenv
from time import sleep

import pytest
from requests.exceptions import ConnectionError

from pyzabbix import ZabbixAPI, ZabbixAPIException

ZABBIX_SERVER = "http://localhost:8888"
ZABBIX_VERSION = getenv("ZABBIX_VERSION", "6.2")


@pytest.fixture(scope="session", autouse=True)
def wait_for_zabbix() -> None:
    max_attempts = 30
    while max_attempts > 0:
        try:
            ZabbixAPI(ZABBIX_SERVER).apiinfo.version()
        except (ConnectionError, ZabbixAPIException):
            sleep(2)
            max_attempts -= 1
            continue
        break

    if max_attempts <= 0:
        pytest.exit("waiting for zabbix failed!", 1)


@pytest.fixture()
def zapi() -> ZabbixAPI:
    api = ZabbixAPI(ZABBIX_SERVER)
    api.login("Admin", "zabbix")
    return api
