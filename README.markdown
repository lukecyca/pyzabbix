# PyZabbix #

**PyZabbix** is a Python module for working with the [Zabbix API](https://www.zabbix.com/documentation/current/manual/api/reference).

[![Build Status](https://travis-ci.org/lukecyca/pyzabbix.png?branch=master)](https://travis-ci.org/lukecyca/pyzabbix)
[![PyPi version](https://img.shields.io/pypi/v/pyzabbix.svg)](https://pypi.python.org/pypi/pyzabbix/)

## Requirements
* Tested against Zabbix 1.8 through 5.0

## Documentation ##
### Getting Started

Install PyZabbix using pip:

```bash
$ pip install pyzabbix
```

You can now import and use pyzabbix like so:

```python
from pyzabbix import ZabbixAPI

zapi = ZabbixAPI("http://zabbixserver.example.com")
zapi.login("zabbix user", "zabbix pass")
# You can also authenticate using an API token instead of user/pass with Zabbix >= 5.4
# zapi.login(api_token='xxxxx')
print("Connected to Zabbix API Version %s" % zapi.api_version())

for h in zapi.host.get(output="extend"):
    print(h['hostid'])
```
Refer to the [Zabbix API Documentation](https://www.zabbix.com/documentation/current/manual/api/reference) and the [PyZabbix Examples](https://github.com/lukecyca/pyzabbix/tree/master/examples) for more information.

### Customizing the HTTP request
PyZabbix uses the [requests](https://requests.readthedocs.io/en/master/) library for HTTP. You can customize the request parameters by configuring the [requests Session](https://requests.readthedocs.io/en/master/user/advanced/#session-objects) object used by PyZabbix.

This is useful for:
* Customizing headers
* Enabling HTTP authentication
* Enabling Keep-Alive
* Disabling SSL certificate verification

```python
from pyzabbix import ZabbixAPI

zapi = ZabbixAPI("http://zabbixserver.example.com")

# Enable HTTP auth
zapi.session.auth = ("http user", "http password")

# Disable SSL certificate verification
zapi.session.verify = False

# Specify a timeout (in seconds)
zapi.timeout = 5.1

# Login (in case of HTTP Auth, only the username is needed, the password, if passed, will be ignored)
zapi.login("http user", "http password")

# You can also authenticate using an API token instead of user/pass with Zabbix >= 5.4
# zapi.login(api_token='xxxxx')
```

### Enabling debug logging
If you need to debug some issue with the Zabbix API, you can enable the output of logging, pyzabbix already uses the default python logging facility but by default, it logs to "Null", you can change this behavior on your program, here's an example:
```python
import sys
import logging
from pyzabbix import ZabbixAPI

stream = logging.StreamHandler(sys.stdout)
stream.setLevel(logging.DEBUG)
log = logging.getLogger('pyzabbix')
log.addHandler(stream)
log.setLevel(logging.DEBUG)


zapi = ZabbixAPI("http://zabbixserver.example.com")
zapi.login('admin','password')

# You can also authenticate using an API token instead of user/pass with Zabbix >= 5.4
# zapi.login(api_token='xxxxx')

```
The expected output is as following:

```
Sending: {
    "params": {
        "password": "password",
        "user": "admin"
    },
    "jsonrpc": "2.0",
    "method": "user.login",
    "id": 2
}
Response Code: 200
Response Body: {
    "jsonrpc": "2.0",
    "result": ".................",
    "id": 2
}
>>>
```

## License ##
LGPL 2.1   http://www.gnu.org/licenses/old-licenses/lgpl-2.1.html

Zabbix API Python Library.

Original Ruby Library is Copyright (C) 2009 Andrew Nelson nelsonab(at)red-tux(dot)net

Original Python Library is Copyright (C) 2009 Brett Lentz brett.lentz(at)gmail(dot)com

This library is free software; you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public
License as published by the Free Software Foundation; either
version 2.1 of the License, or (at your option) any later version.

This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public
License along with this library; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
