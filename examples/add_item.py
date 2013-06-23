"""
Looks up a host based on its name, and then adds an item to it
"""

from pyzabbix import ZabbixAPI

# The hostname at which the Zabbix web interface is available
ZABBIX_SERVER = 'https://zabbix.example.com'

zapi = ZabbixAPI(ZABBIX_SERVER)

# Login to the Zabbix API
zapi.login('api_username', 'api_password')

host_name = 'example.com'

hosts = zapi.host.get(filter={"host": host_name})
if hosts:
    host_id = hosts[0]["hostid"]
    print("Found host id {0}".format(host_id))

    zapi.item.create(
        hostid=host_id,
        description='Used disk space on $1 in %',
        key_='vfs.fs.size[/,pused]',
    )
else:
    print("No hosts found")
