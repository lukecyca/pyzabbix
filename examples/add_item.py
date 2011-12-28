"""
Looks up a host based on its name, and then adds an item to it
"""

from getpass import getpass
from pyzabbix import ZabbixAPI

# The hostname at which the Zabbix web interface is available
ZABBIX_SERVER = 'https://zabbix.example.com'

# Enter credentials for the Zabbix Web Frontend
username = raw_input('Username: ')
password = getpass()

# Connect to the Zabbix web frontend (using the same credentials for HTTPAUTH)
zapi = ZabbixAPI(ZABBIX_SERVER, username, password)

# Login to the Zabbix web frontend / API
zapi.login(username, password)

host_name = raw_input('Add item to what host: ')

hosts = zapi.host.get(filter={"host": host_name})
if hosts:
    host_id = hosts[0]["hostid"]
    print "Found host id {0}".format(host_id)

    zapi.item.create(hostid=host_id,
                     description='Used disk space on $1 in %',
                     key_='vfs.fs.size[/,pused]',
                     )
else:
    print "No hosts found"




