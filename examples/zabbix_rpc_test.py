#!/usr/bin/python
import optparse
import sys
import traceback
from getpass import getpass
from zabbix_api import ZabbixAPI, ZabbixAPIException

def get_options():
    """ command-line options """

    usage = "usage: %prog [options]"
    OptionParser = optparse.OptionParser
    parser = OptionParser(usage)

    parser.add_option("-s", "--server", action="store", type="string", \
            dest="server", help="Zabbix Server URL (REQUIRED)")
    parser.add_option("-u", "--username", action="store", type="string", \
            dest="username", help="Username (Will prompt if not given)")
    parser.add_option("-p", "--password", action="store", type="string", \
            dest="password", help="Password (Will prompt if not given)")

    options, args = parser.parse_args()

    if not options.server:
        show_help(parser)

    if not options.username:
        options.username = raw_input('Username: ')

    if not options.password:
        options.password = getpass()

    # apply clue to user...
    if not options.username and not options.password:
        show_help(parser)

    return options, args

def show_help(p):
    p.print_help()
    print "NOTE: Zabbix 1.8.0 doesn't check LDAP when authenticating."
    sys.exit(-1)

def errmsg(msg):
    sys.stderr.write(msg + "\n")
    sys.exit(-1)

if  __name__ == "__main__":
    options, args = get_options()

    zapi = ZabbixAPI(server=options.server,log_level=3)

    try:
        zapi.login(options.username, options.password)
        print "Zabbix API Version: %s" % zapi.api_version()
        print "Logged in: %s" % str(zapi.test_login())
    except ZabbixAPIException, e:
        sys.stderr.write(str(e) + '\n')

    try:
        for host in zapi.host.get({ 'monitored_hosts' : True,'extendoutput' : True}):
            if host['dns'] == "":
                print "%s - %s - %s" % (host['host'], host['ip'], host['useip'])
            else:
                print "%s - %s - %s" % (host['dns'], host['ip'], host['useip'])

            if host['useip'] == "1" and host['dns'] != "":
                print "Updating %s to monitor by FQDN." % host['dns']
                newhost = host
                newhost['useip'] = 0
                zapi.host.update(newhost)

    except ZabbixAPIException, e:
        sys.stderr.write(str(e) + '\n')
