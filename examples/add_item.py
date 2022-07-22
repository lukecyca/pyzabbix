"""
Looks up a host based on its name, and then adds an item to it
"""

import sys

from pyzabbix import ZabbixAPI, ZabbixAPIException

# The hostname at which the Zabbix web interface is available
ZABBIX_SERVER = "https://zabbix.example.com"

zapi = ZabbixAPI(ZABBIX_SERVER)

# Login to the Zabbix API
zapi.login("Admin", "zabbix")

host_name = "example.com"

hosts = zapi.host.get(filter={"host": host_name}, selectInterfaces=["interfaceid"])
if hosts:
    host_id = hosts[0]["hostid"]
    print(f"Found host id {host_id}")

    try:
        item = zapi.item.create(
            hostid=host_id,
            name="Used disk space on $1 in %",
            key_="vfs.fs.size[/,pused]",
            type=0,
            value_type=3,
            interfaceid=hosts[0]["interfaces"][0]["interfaceid"],
            delay=30,
        )
    except ZabbixAPIException as e:
        print(e)
        sys.exit()
    print("Added item with itemid {} to host: {}".format(item["itemids"][0], host_name))
else:
    print("No hosts found")
