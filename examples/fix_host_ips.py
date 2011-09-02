import sys
import socket
from getpass import getpass
from pyzabbix import ZabbixAPI

# The hostname at which the Zabbix web interface is available
zabbix_server = 'http://localhost'


def update_host_ip(zapi,hostid,ip):
    try:
        zapi.host.update(
            hostid=hostid,
            ip=ip
            )
    except zabbix_api2.ZabbixAPIException as e:
        print e



def main():

    # Enter administrator credentials for the Zabbix Web Frontend
    username = raw_input('Username: ')
    password = getpass()

    zapi = ZabbixAPI(zabbix_server, username, password)
    zapi.login(username, password)
    print "Connected to Zabbix API Version %s" % zapi.api_version()

    for h in zapi.host.get(extendoutput=True):
        # Make sure the hosts are named according to their FQDN
        if h['dns'] != h['host']:
            print '%s is actually connecting to %s.' % (h['host'],h['dns'])

        # Make sure they are using hostnames to connect rather than IPs
        if h['useip'] == '1':
            print '%s is using IP instead of hostname. Skipping.' % h['host']
            continue

        # Set their IP record to match what the DNS system says it should be
        try:
            lookup = socket.gethostbyaddr(h['dns'])
        except socket.gaierror, e:
            print h['dns'], e
            continue
        actual_ip = lookup[2][0]
        if actual_ip != h['ip']:
            print "%s has the wrong IP: %s. Changing it to: %s" % (h['host'], h['ip'], actual_ip)
            update_host_ip(zapi,h['hostid'],actual_ip)




if __name__ == "__main__":
    main()