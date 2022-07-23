from pyzabbix import ZabbixAPI

from .conftest import ZABBIX_VERSION


def test_login(zapi: ZabbixAPI) -> None:
    assert zapi.auth


def test_version(zapi: ZabbixAPI) -> None:
    assert zapi.api_version().startswith(ZABBIX_VERSION)


def test_host_get(zapi: ZabbixAPI) -> None:
    hosts = zapi.host.get(filter={"host": ["Zabbix server"]})
    assert hosts[0]["host"] == "Zabbix server"


def test_host_update_interface(zapi: ZabbixAPI) -> None:
    hosts = zapi.host.get(filter={"host": ["Zabbix server"]}, output="extend")
    assert hosts[0]["host"] == "Zabbix server"

    interfaces = zapi.hostinterface.get(hostids=hosts[0]["hostid"])
    assert interfaces[0]["ip"] == "127.0.0.1"

    interfaces_update = zapi.hostinterface.update(
        interfaceid=interfaces[0]["interfaceid"],
        dns="zabbix-agent",
    )
    assert interfaces_update["interfaceids"] == [interfaces[0]["interfaceid"]]

    interfaces = zapi.hostinterface.get(hostids=hosts[0]["hostid"])
    assert interfaces[0]["dns"] == "zabbix-agent"
