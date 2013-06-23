"""
Zabbix stores the DNS name and the IP for each host that it monitors, and
uses one or the other to connect to the host.  It is good practice to make
sure the IP and DNS name are both correct.  This script checks the DNS and
IP for all hosts in Zabbix, compares the IP against an actual DNS lookup,
and fixes it if required.
"""

import socket
from getpass import getpass
from pyzabbix import ZabbixAPI, ZabbixAPIException

# The hostname at which the Zabbix web interface is available
ZABBIX_SERVER = 'https://zabbix.example.com'

zapi = ZabbixAPI(ZABBIX_SERVER)

# Login to the Zabbix API
zapi.login('api_username', 'api_password')

# Loop through all hosts
for h in zapi.host.get(extendoutput=True):
    # Make sure the hosts are named according to their FQDN
    if h['dns'] != h['host']:
        print('Warning: %s has dns "%s"' % (h['host'], h['dns']))

    # Make sure they are using hostnames to connect rather than IPs
    if h['useip'] == '1':
        print('%s is using IP instead of hostname. Skipping.' % h['host'])
        continue

    # Do a DNS lookup for the host's DNS name
    try:
        lookup = socket.gethostbyaddr(h['dns'])
    except socket.gaierror as e:
        print(h['dns'], e)
        continue
    actual_ip = lookup[2][0]

    # Check whether the looked-up IP matches the one stored in the host's IP
    # field
    if actual_ip != h['ip']:
        print("%s has the wrong IP: %s. Changing it to: %s" % (h['host'],
                                                               h['ip'],
                                                               actual_ip))

        # Set the host's IP field to match what the DNS lookup said it should
        # be
        try:
            zapi.host.update(hostid=h['hostid'], ip=actual_ip)
        except ZabbixAPIException as e:
            print(e)
