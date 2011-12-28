"""
Retrieves trend data for a given item_id
"""

from getpass import getpass
from pyzabbix import ZabbixAPI
from datetime import datetime
import time

# The hostname at which the Zabbix web interface is available
ZABBIX_SERVER = 'https://zabbix.example.com'

# Enter credentials for the Zabbix Web Frontend
username = raw_input('Username: ')
password = getpass()

# Connect to the Zabbix web frontend (using the same credentials for HTTPAUTH)
zapi = ZabbixAPI(ZABBIX_SERVER, username, password)

# Login to the Zabbix web frontend / API
zapi.login(username, password)

item_id = raw_input('Get data for what item? ')

# Create a time range
time_till = time.mktime(datetime.now().timetuple())
time_from = time_till - 60 * 60 * 4 # 4 hours

# Query item's trend data
history = zapi.history.get(itemids=[item_id],
                                  time_from=time_from,
                                  time_till=time_till,
                                  output='extend',
                                  limit='5000',
                                  )

# If nothing was found, try getting it from history
if len(history) == 0:
    history = zapi.history.get(itemids=[item_id],
                                      time_from=time_from,
                                      time_till=time_till,
                                      output='extend',
                                      limit='5000',
                                      history=0,
                                      )

# Print out each datapoint
for point in history:
    print "{0}: {1}".format(datetime.fromtimestamp(int(point['clock'])).strftime("%x %X"),
                            point['value'])
