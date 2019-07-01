"""
Prints hostnames for all known hosts.
"""

from pyzabbix import ZabbixAPI

ZABBIX_SERVER = 'https://zabbix.example.com'

# Use context manager to auto-logout after request is done.
with ZabbixAPI(ZABBIX_SERVER) as zapi:
    zapi.login('api_username', 'api_password')
    hosts = zapi.host.get(output=['name'])
    for host in hosts:
        print(host['name'])
