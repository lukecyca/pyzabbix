"""
Set connect and read timeout for ZabbixAPI requests
"""

from pyzabbix import ZabbixAPI

# The hostname at which the Zabbix web interface is available
ZABBIX_SERVER = 'https://zabbix.example.com'

# Timeout (float) in seconds
# By default this timeout affects both the "connect" and "read", but
# if you are using Requests library > v2.4.0 you can specify the timeout as a tuple (connect, read)
# to set individual timeouts.
TIMEOUT = 3.5

# You can define the timeout while creating the ZabbixAPI object:
zapi = ZabbixAPI(ZABBIX_SERVER, timeout=TIMEOUT)

# Login to the Zabbix API
zapi.login('api_username', 'api_password')

# Or you can re-define it after
zapi.timeout = TIMEOUT
