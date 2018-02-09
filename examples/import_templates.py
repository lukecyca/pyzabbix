"""                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        
Import Zabbix XML templates
"""                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           
from pyzabbix import ZabbixAPI, ZabbixAPIException
import os
import sys                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 

if len(sys.argv) <= 1:
    print('Please provide directory with templates as first ARG or the XML file with template.')
    exit(1)

path = sys.argv[1]

# The hostname at which the Zabbix web interface is available
ZABBIX_SERVER = 'https://zabbix.example.org'

zapi = ZabbixAPI(ZABBIX_SERVER)

# Login to the Zabbix API
#zapi.session.verify = False
zapi.login("Admin", "zabbix")

rules = {
    'applications': {
        'createMissing': True,
    },
    'discoveryRules': {
        'createMissing': True,
        'updateExisting': True
    },
    'graphs': {
        'createMissing': True,
        'updateExisting': True
    },
    'groups': {
        'createMissing': True
    },
    'hosts': {
        'createMissing': True,
        'updateExisting': True
    },
    'images': {
        'createMissing': True,
        'updateExisting': True
    },
    'items': {
        'createMissing': True,
        'updateExisting': True
    },
    'maps': {
        'createMissing': True,
        'updateExisting': True
    },
    'screens': {
        'createMissing': True,
        'updateExisting': True
    },
    'templateLinkage': {
        'createMissing': True,
    },
    'templates': {
        'createMissing': True,
        'updateExisting': True
    },
    'templateScreens': {
        'createMissing': True,
        'updateExisting': True
    },
    'triggers': {
        'createMissing': True,
        'updateExisting': True
    },
    'valueMaps': {
        'createMissing': True,
        'updateExisting': True
    },
}

if os.path.isdir(path):
    #path = path/*.xml
    files = glob.glob(path+'/*.xml')
    for file in files:
        print(file)
        with open(file, 'r') as f:
            template = f.read()
            try:
                zapi.confimport('xml', template, rules)
            except ZabbixAPIException as e:
                print(e)
        print('')
elif os.path.isfile(path):
    files = glob.glob(path)
    for file in files:
        with open(file, 'r') as f:
            template = f.read()
            try:
                zapi.confimport('xml', template, rules)
            except ZabbixAPIException as e:
                print(e)
else:
    print('I need a xml file')
